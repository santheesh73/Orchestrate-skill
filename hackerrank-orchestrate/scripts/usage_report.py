#!/usr/bin/env python3
"""Build evaluation/usage_report.md from a per-call JSONL token log.

Failure it prevents: a missing or hand-estimated usage report, which the September
2026 contract made a required file inside code.zip.

Each JSONL line is one model call (see assets/usage_log_schema.md):
  {"provider": "anthropic", "model": "<id>", "request_id": "r_001",
   "input_tokens": 1234, "output_tokens": 210, "run_id": "final"}

Prices change, so none are built in. Pass them per model in USD per million tokens:
  --price "<model id>=3:15"    (input 3 $/MTok, output 15 $/MTok)
Optionally add cache prices: --price "<model id>=3:15:0.3:3.75" (cache read, cache write).
Models without a price are reported with cost "not estimated".

Example:
  python usage_report.py evaluation/usage.jsonl --run-id final \
      --price "model-a=3:15" --requests 250 --out code/evaluation/usage_report.md

Standard library only.

Exit 0 when the report is written, 2 on usage errors (unreadable or malformed log,
bad --price, an --out path that cannot be written). --out creates missing parent folders.
"""

import argparse
import json
import math
import os
import stat
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone


def parse_price(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"--price must look like model=in:out, got {spec!r}")
    model, nums = spec.rsplit("=", 1)
    parts = nums.split(":")
    if len(parts) not in (2, 4):
        raise argparse.ArgumentTypeError(f"--price needs in:out or in:out:cache_read:cache_write, got {nums!r}")
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError(f"--price values must be numbers, got {nums!r}")
    if not all(math.isfinite(v) and v >= 0 for v in vals):
        raise argparse.ArgumentTypeError(f"--price values must be finite and not negative, got {nums!r}")
    if len(vals) == 2:
        vals += [None, None]
    return model.strip(), vals


def positive_int(text):
    try:
        n = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a whole number, got {text!r}")
    if n < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {n}")
    return n


TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def record_error(rec):
    """Why a parsed log line cannot be counted, or None. Wrong types used to crash or be summed."""
    if not isinstance(rec, dict):
        return "is not a JSON object"
    missing = [k for k in ("provider", "model", "input_tokens", "output_tokens") if k not in rec]
    if missing:
        return f"is missing {missing}"
    if not (isinstance(rec["provider"], str) and isinstance(rec["model"], str)):
        return "has a provider or model that is not a string"
    for k in TOKEN_FIELDS:
        v = rec.get(k)
        if v is None and k not in ("input_tokens", "output_tokens"):
            continue
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return f"has {k} = {v!r}; token counts must be whole numbers, not negative"
    return None


def fmt_int(n):
    return f"{int(n):,}"


def fmt_cost(c):
    return "not estimated" if c is None else f"${c:,.4f}"


def overwrites_input(out, inputs):
    """True when --out names a file this run reads (AGENTS.md, a source file, the log)."""
    if not os.path.isfile(out):
        return False
    return any(os.path.isfile(i) and os.path.samefile(out, i) for i in inputs)


def special_files(args):
    """Path arguments that are named pipes or sockets: reading one with no writer hangs."""
    found = []
    for v in vars(args).values():
        for x in v if isinstance(v, list) else [v]:
            try:
                if isinstance(x, str) and stat.S_ISFIFO(os.stat(x).st_mode) | stat.S_ISSOCK(os.stat(x).st_mode):
                    found.append(x)
            except (OSError, ValueError):
                pass
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="JSONL file, one object per model call")
    ap.add_argument("--run-id", help="only include calls with this run_id (the final full run)")
    ap.add_argument("--price", action="append", default=[], type=parse_price, help="model=in:out[:cache_read:cache_write] in $/MTok")
    ap.add_argument("--requests", type=positive_int, help="number of input rows in the run (default: distinct request_id values)")
    ap.add_argument("--title", default="Token usage and cost report")
    ap.add_argument("--out", help="write the report here (default: stdout)")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2
    prices = dict(args.price)

    stats = OrderedDict()
    request_ids = set()
    skipped = 0
    try:
        fh = open(args.log, encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    with fh:
        try:
            lines = fh.read().splitlines()
        except UnicodeDecodeError:
            print(f"error: {args.log} is not valid UTF-8", file=sys.stderr)
            return 2
        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, RecursionError):  # RecursionError: nested too deeply
                print(f"error: line {lineno} is not valid JSON", file=sys.stderr)
                return 2
            if args.run_id is not None and isinstance(rec, dict) and str(rec.get("run_id")) != args.run_id:
                skipped += 1
                continue
            problem = record_error(rec)
            if problem:
                print(f"error: line {lineno} {problem}", file=sys.stderr)
                return 2
            key = (rec["provider"], rec["model"])
            s = stats.setdefault(key, defaultdict(int))
            s["calls"] += 1
            s["input"] += int(rec["input_tokens"])
            s["output"] += int(rec["output_tokens"])
            s["cache_read"] += int(rec.get("cache_read_input_tokens") or 0)
            s["cache_write"] += int(rec.get("cache_creation_input_tokens") or 0)
            if rec.get("request_id") not in (None, ""):
                request_ids.add(str(rec["request_id"]))

    if not stats:
        print("error: no calls found" + (f" for run_id {args.run_id!r}" if args.run_id else ""), file=sys.stderr)
        return 2

    n_requests = args.requests or len(request_ids)
    if not n_requests:
        print("error: pass --requests; no request_id values in the log", file=sys.stderr)
        return 2

    def cost(model, s):
        p = prices.get(model)
        if p is None:
            return None
        pin, pout, pcr, pcw = p
        c = s["input"] * pin + s["output"] * pout
        if s["cache_read"]:
            if pcr is None:
                return None
            c += s["cache_read"] * pcr
        if s["cache_write"]:
            if pcw is None:
                return None
            c += s["cache_write"] * pcw
        return c / 1_000_000

    any_cache = any(s["cache_read"] or s["cache_write"] for s in stats.values())
    total = defaultdict(int)
    total_cost = 0.0
    cost_complete = True
    rows = []
    for (provider, model), s in stats.items():
        c = cost(model, s)
        if c is None:
            cost_complete = False
        else:
            total_cost += c
        for k, v in s.items():
            total[k] += v
        rows.append((provider, model, s, c))

    out = []
    out.append(f"# {args.title}\n")
    out.append(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from `{args.log}`"
               + (f", run `{args.run_id}`" if args.run_id else "") + ".\n")
    out.append("This report covers the final full-dataset run that produced `output.csv`.\n")
    out.append("## Summary\n")
    out.append("| Metric | Value |\n|---|---|")
    out.append(f"| Requests processed | {fmt_int(n_requests)} |")
    out.append(f"| Model calls | {fmt_int(total['calls'])} |")
    out.append(f"| Input tokens | {fmt_int(total['input'])} |")
    out.append(f"| Output tokens | {fmt_int(total['output'])} |")
    if any_cache:
        out.append(f"| Cache read input tokens | {fmt_int(total['cache_read'])} |")
        out.append(f"| Cache write input tokens | {fmt_int(total['cache_write'])} |")
    all_tokens = total["input"] + total["output"] + total["cache_read"] + total["cache_write"]
    out.append(f"| Total tokens | {fmt_int(all_tokens)} |")
    out.append(f"| Average tokens per request | {all_tokens / n_requests:,.1f} |")
    out.append(f"| Average model calls per request | {total['calls'] / n_requests:,.2f} |")
    tc = total_cost if cost_complete else None
    out.append(f"| Estimated total cost (USD) | {fmt_cost(tc)} |")
    out.append(f"| Estimated cost per request (USD) | {fmt_cost(None if tc is None else tc / n_requests)} |\n")

    out.append("## Per model\n")
    head = "| Provider | Model | Calls | Input tokens | Output tokens |"
    sep = "|---|---|---|---|---|"
    if any_cache:
        head += " Cache read | Cache write |"
        sep += "---|---|"
    head += " Est. cost (USD) |"
    sep += "---|"
    out.append(head)
    out.append(sep)
    for provider, model, s, c in rows:
        line = f"| {provider} | {model} | {fmt_int(s['calls'])} | {fmt_int(s['input'])} | {fmt_int(s['output'])} |"
        if any_cache:
            line += f" {fmt_int(s['cache_read'])} | {fmt_int(s['cache_write'])} |"
        line += f" {fmt_cost(c)} |"
        out.append(line)
    out.append("")

    out.append("## Pricing used\n")
    if prices:
        for model, (pin, pout, pcr, pcw) in prices.items():
            extra = "" if pcr is None else f", cache read ${pcr}/MTok, cache write ${pcw}/MTok"
            out.append(f"- `{model}`: input ${pin}/MTok, output ${pout}/MTok{extra}")
    else:
        out.append("- No prices supplied; costs not estimated.")
    out.append("\nToken counts come from the provider's per-call usage fields. Costs are estimates from the prices above.")
    report = "\n".join(out) + "\n"

    if args.out:
        if overwrites_input(args.out, [args.log]):
            print(f"error: --out {args.out} is the usage log itself; refusing to overwrite it", file=sys.stderr)
            return 2
        try:
            if os.path.dirname(args.out):
                os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(report)
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc.strerror}", file=sys.stderr)
            return 2
        print(f"wrote {args.out} ({total['calls']} calls, {n_requests} requests"
              + (f", {skipped} calls from other runs skipped" if skipped else "") + ")")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
