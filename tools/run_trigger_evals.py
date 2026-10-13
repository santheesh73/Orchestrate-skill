#!/usr/bin/env python3
"""Measure how well the skill's description triggers on evals/triggers.json.

Failure it prevents: a description that fires on unrelated work (hijacking ordinary
sessions with hackathon rules) or stays silent during the event.

Modes:
  --offline  Deterministic lexical-overlap PROXY: the share of a query's content words
             that appear in the description, compared with a fixed threshold. It is not
             model behavior and says nothing about real trigger accuracy. Used in CI to
             catch descriptions that drift far from their eval set.
  --live     Opt-in. Reads ANTHROPIC_API_KEY from the environment, requires --model, and
             asks the model N times per query (default 3) whether it would load the skill
             given only its name and description. Prints per-query trigger rate, false
             positives, false negatives, precision and recall per split. With no key it
             prints UNKNOWN and exits 0. The key is never printed or written anywhere.
             Never run this in CI.

Splits: each query is assigned to "train" or "test" by a stable hash, so a description
can be tuned on train and reported on test (--split train|test|all).

Exit codes: 0 when done (or live mode without a key, which prints UNKNOWN); 1 when the
offline proxy falls below --min-precision or --min-recall; 2 on usage errors, including
an unreadable, malformed or empty eval file or SKILL.md.

Standard library only. The only network access is --live.
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_EVALS = os.path.join(ROOT, "evals", "triggers.json")
DEFAULT_SKILL = os.path.join(ROOT, "hackerrank-orchestrate", "SKILL.md")
API_URL = "https://api.anthropic.com/v1/messages"
STOPWORDS = set("""a an and are as at be but by can do does for from give go got have how i i'm if in
into is it its me my no not of on or our pls please so than that the their them then there these this
to up us was we what when where which who why will with you your yours am im just get should could would
before after about out off all any via one two""".split())


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9_.=/\-]+", text.lower()) if t not in STOPWORDS and len(t) > 1]


def stems(words):
    out = set()
    for w in words:
        w = w.strip(".-/=")
        if len(w) > 4 and w.endswith("s"):
            w = w[:-1]
        if w:
            out.add(w)
    return out


def read_skill(path):
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError(f"{path} has no frontmatter")
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields.get("name", ""), fields.get("description", "")


def split_of(query):
    return "test" if int(hashlib.sha256(query.encode("utf-8")).hexdigest(), 16) % 3 == 0 else "train"


def load_evals(path, split):
    with open(path, encoding="utf-8-sig") as fh:
        evals = json.load(fh)
    if not (isinstance(evals, list) and evals and all(
            isinstance(e, dict) and isinstance(e.get("query"), str) and isinstance(e.get("should_trigger"), bool)
            for e in evals)):
        raise ValueError(f"{path} must be a non-empty JSON list of {{\"query\": str, \"should_trigger\": bool}}")
    for e in evals:
        e["split"] = split_of(e["query"])
    return [e for e in evals if split == "all" or e["split"] == split]


def summarize(results, label):
    tp = sum(1 for r in results if r["expected"] and r["triggered"])
    fp = sum(1 for r in results if not r["expected"] and r["triggered"])
    fn = sum(1 for r in results if r["expected"] and not r["triggered"])
    tn = sum(1 for r in results if not r["expected"] and not r["triggered"])
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    fmt = lambda x: "n/a" if x is None else f"{x:.2f}"
    print(f"{label}: n={len(results)} TP={tp} FP={fp} FN={fn} TN={tn} precision={fmt(precision)} recall={fmt(recall)}")
    return precision, recall


def offline(args, name, desc, evals):
    d = stems(tokens(name.replace("-", " ") + " " + desc))
    results = []
    for e in evals:
        q = stems(tokens(e["query"]))
        score = len(q & d) / len(q) if q else 0.0
        results.append({"query": e["query"], "expected": e["should_trigger"], "score": score,
                        "triggered": score >= args.threshold, "split": e["split"]})
    print("OFFLINE PROXY: lexical overlap with the description, threshold "
          f"{args.threshold}. This is not model behavior and is not a trigger-accuracy measurement.\n")
    for r in results:
        if r["triggered"] != r["expected"]:
            kind = "FALSE POSITIVE" if r["triggered"] else "FALSE NEGATIVE"
            print(f"  {kind:<15} score={r['score']:.2f} [{r['split']}] {r['query'][:90]}")
    print()
    p, r = summarize(results, "proxy " + args.split)
    failed = (args.min_precision is not None and (p or 0) < args.min_precision) or \
             (args.min_recall is not None and (r or 0) < args.min_recall)
    if failed:
        print(f"proxy below floor (min precision {args.min_precision}, min recall {args.min_recall})")
    return 1 if failed else 0


def ask(model, key, name, desc, query, timeout):
    prompt = (
        "You are deciding whether to load a skill before answering a user. You see only the skill's "
        "name and description.\n\n"
        f"Skill name: {name}\nSkill description: {desc}\n\n"
        f"User message:\n<<<\n{query}\n>>>\n\n"
        "Would you load this skill to answer the user message? Reply with exactly YES or NO."
    )
    body = json.dumps({"model": model, "max_tokens": 5,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return text.strip().upper().startswith("YES")


def live(args, name, desc, evals):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("UNKNOWN: ANTHROPIC_API_KEY is not set, so live trigger accuracy was not measured.")
        return 0
    if not args.model:
        print("error: --live needs --model (no model id is built in)", file=sys.stderr)
        return 2
    results = []
    for e in evals:
        hits, errors = 0, 0
        for _ in range(args.runs):
            try:
                hits += ask(args.model, key, name, desc, e["query"], args.timeout)
            except (urllib.error.URLError, OSError, ValueError) as exc:
                errors += 1
                # Never echo request headers; the exception text does not contain the key.
                print(f"  request failed: {type(exc).__name__}", file=sys.stderr)
            time.sleep(args.delay)
        done = args.runs - errors
        rate = hits / done if done else None
        results.append({"query": e["query"], "expected": e["should_trigger"], "rate": rate,
                        "triggered": rate is not None and rate >= 0.5, "split": e["split"]})
        shown = "UNKNOWN" if rate is None else f"{rate:.2f}"
        print(f"  rate={shown} expected={'yes' if e['should_trigger'] else 'no'} [{e['split']}] {e['query'][:80]}")
    measured = [r for r in results if r["rate"] is not None]
    print(f"\nLIVE: model {args.model}, {args.runs} runs per query, trigger = rate >= 0.5")
    for r in measured:
        if r["triggered"] != r["expected"]:
            print(f"  {'FALSE POSITIVE' if r['triggered'] else 'FALSE NEGATIVE'}: {r['query'][:90]}")
    for s in ("train", "test"):
        sub = [r for r in measured if r["split"] == s]
        if sub:
            summarize(sub, f"live {s}")
    if len(measured) < len(results):
        print(f"{len(results) - len(measured)} queries UNKNOWN (all requests failed)")
    return 0


def bounded_int(low):
    """argparse type: a whole number of at least low (out-of-range values used to be accepted)."""
    def parse(text):
        try:
            n = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"expected a whole number, got {text!r}")
        if n < low:
            raise argparse.ArgumentTypeError(f"must be at least {low}, got {n}")
        return n
    return parse


def bounded_float(low, high=None):
    """argparse type: a finite number in [low, high] (NaN and out-of-range values used to be accepted)."""
    def parse(text):
        try:
            x = float(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"expected a number, got {text!r}")
        if not math.isfinite(x) or x < low or (high is not None and x > high):
            rng = f"between {low} and {high}" if high is not None else f"at least {low}"
            raise argparse.ArgumentTypeError(f"must be {rng}, got {text!r}")
        return x
    return parse


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="deterministic lexical proxy (no network)")
    mode.add_argument("--live", action="store_true", help="opt-in model run; needs ANTHROPIC_API_KEY and --model")
    ap.add_argument("--evals", default=DEFAULT_EVALS)
    ap.add_argument("--skill", default=DEFAULT_SKILL, help="SKILL.md whose name and description are tested")
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--threshold", type=bounded_float(0, 1), default=0.3, help="offline: overlap share that counts as a trigger")
    ap.add_argument("--min-precision", type=bounded_float(0, 1), help="offline: exit 1 if proxy precision is below this")
    ap.add_argument("--min-recall", type=bounded_float(0, 1), help="offline: exit 1 if proxy recall is below this")
    ap.add_argument("--model", help="live: model id to query (required for --live)")
    ap.add_argument("--runs", type=bounded_int(1), default=3, help="live: runs per query")
    ap.add_argument("--timeout", type=bounded_int(1), default=60, help="live: seconds per request")
    ap.add_argument("--delay", type=bounded_float(0), default=0.2, help="live: seconds between requests")
    args = ap.parse_args(argv)

    try:
        name, desc = read_skill(args.skill)
        evals = load_evals(args.evals, args.split)
    except (OSError, ValueError, RecursionError) as exc:  # bad or too deeply nested JSON, non-UTF-8 bytes
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.offline:
        return offline(args, name, desc, evals)
    return live(args, name, desc, evals)


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
