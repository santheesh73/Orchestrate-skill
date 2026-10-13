#!/usr/bin/env python3
"""Extract the requirement lines from a starter repo's AGENTS.md and problem_statement.md.

Failure it prevents: missing a new MUST in the first 15 minutes of an edition (a new
required file, a new log rule, a changed column list) because the contract was read
from memory of the last edition.

HEURISTIC: it finds lines by keywords and shapes. It never replaces reading the files
in full; treat its output as a checklist to confirm against them.

Categories:
  must          lines with must / required / mandatory / always / exactly / only
  must_not      lines with must not / never / do not / don't / forbidden / invalid
  required_file file paths named on a requirement line (for example evaluation/usage_report.md)
  columns       comma-separated identifier lists of 3+ fields inside code blocks
  allowed       "is one of" / "one of `a`, `b`" lines
  order         numbered items following a line about prefer / order / tie-break / conflict

Usage:
  contract_extract.py STARTER_DIR                 checklist for one edition
  contract_extract.py --diff OLD_DIR NEW_DIR      added / changed / removed requirements

Each line carries its source file:line. Standard library only.

Exit 0 when the checklist or diff is written, 2 on usage errors (missing starter files,
unreadable input, an --out path that cannot be written), 3 when no requirement line was
found at all (an empty checklist is not a clean contract; read the files by hand).
--out creates missing parent folders.
"""

import argparse
import difflib
import os
import re
import stat
import sys

FILES = ("AGENTS.md", "problem_statement.md")
MUST_NOT = re.compile(r"\b(must not|never|do not|don't|forbidden|not allowed|invalid|off limits)\b", re.I)
MUST = re.compile(r"\b(must|required|mandatory|always|exactly|only)\b", re.I)
ALLOWED = re.compile(r"\b(is one of|one of\s+`|allowed values?)\b", re.I)
ORDER_LEAD = re.compile(r"\b(prefer|tie-?break|in this order|conflict|order:)\b", re.I)
NUMBERED = re.compile(r"^\s*\d+\.\s+\S")
FILE_RE = re.compile(r"`?([A-Za-z0-9_\-./]+/[A-Za-z0-9_\-.]+\.(?:md|csv|txt|json|zip|py)|[A-Za-z0-9_\-]+\.(?:md|csv|txt|json|zip))`?")
COLUMNS = re.compile(r"^[a-z_][a-z0-9_]*(,[a-z_][a-z0-9_]*){2,}$")
CATEGORIES = ("must", "must_not", "required_file", "columns", "allowed", "order")


def clean(line):
    return re.sub(r"\s+", " ", line.strip().lstrip("-*> ").strip())


def extract_file(path, label):
    items = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    in_code, order_mode = False, False
    for n, raw in enumerate(lines, 1):
        s = raw.strip()
        where = f"{label}:{n}"
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            if COLUMNS.match(s):
                items.append(("columns", s, where))
            continue
        if not s:
            if order_mode and items and items[-1][0] == "order":
                order_mode = False
            continue
        text = clean(s)
        if NUMBERED.match(s) and order_mode:
            items.append(("order", text, where))
            continue
        order_mode = bool(ORDER_LEAD.search(s)) and s.endswith(":")
        if ALLOWED.search(s):
            items.append(("allowed", text, where))
        if MUST_NOT.search(s):
            items.append(("must_not", text, where))
        elif MUST.search(s):
            items.append(("must", text, where))
        if MUST.search(s) or MUST_NOT.search(s) or re.search(r"\b(include|submit|produce|write)\b", s, re.I):
            for m in FILE_RE.finditer(s):
                items.append(("required_file", m.group(1), where))
    return items


def extract_dir(directory):
    items = []
    found = False
    for name in FILES:
        p = os.path.join(directory, name)
        if os.path.exists(p):
            found = True
            items += extract_file(p, name)
    if not found:
        raise FileNotFoundError(f"neither {' nor '.join(FILES)} found in {directory}")
    seen, out = set(), []
    for cat, text, where in items:
        if (cat, text) not in seen:
            seen.add((cat, text))
            out.append((cat, text, where))
    return out


def norm(text):
    t = text.lower()
    t = re.sub(r"\d{4}-\d{2}-\d{2}t?[\d:+\-]*", "<date>", t)
    t = re.sub(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}", "<date>", t)
    t = re.sub(r"(june|september|october|may|august)\d{2}", "<edition>", t)
    return re.sub(r"\s+", " ", t).strip()


def render(items):
    out = ["# Contract checklist (heuristic; confirm against the files)", ""]
    for cat in CATEGORIES:
        rows = [(t, w) for c, t, w in items if c == cat]
        if rows:
            out += [f"## {cat} ({len(rows)})", ""] + [f"- [ ] {t}  ({w})" for t, w in rows] + [""]
    return "\n".join(out)


def diff(old_items, new_items):
    out = ["# Contract diff (heuristic; confirm against the files)", ""]
    for cat in CATEGORIES:
        old = {norm(t): (t, w) for c, t, w in old_items if c == cat}
        new = {norm(t): (t, w) for c, t, w in new_items if c == cat}
        removed = [k for k in old if k not in new]
        added = [k for k in new if k not in old]
        changed = []
        for k in list(added):
            best = difflib.get_close_matches(k, removed, n=1, cutoff=0.6)
            if best:
                changed.append((best[0], k))
                added.remove(k)
                removed.remove(best[0])
        if not (added or removed or changed):
            continue
        out += [f"## {cat}", ""]
        out += [f"+ ADDED   {new[k][0]}  ({new[k][1]})" for k in added]
        out += [f"~ CHANGED {old[a][0]}  ({old[a][1]})\n          -> {new[b][0]}  ({new[b][1]})" for a, b in changed]
        out += [f"- REMOVED {old[k][0]}  ({old[k][1]})" for k in removed]
        out.append("")
    if len(out) == 2:
        out.append("No requirement lines differ.")
    return "\n".join(out)


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
    ap.add_argument("starter", nargs="?", help="directory holding AGENTS.md and/or problem_statement.md")
    ap.add_argument("--diff", nargs=2, metavar=("OLD_DIR", "NEW_DIR"), help="compare two editions")
    ap.add_argument("--out", help="write markdown here (default: stdout)")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2
    try:
        if args.diff:
            old, new = extract_dir(args.diff[0]), extract_dir(args.diff[1])
            found = len(old) + len(new)
            report = diff(old, new)
        elif args.starter:
            items = extract_dir(args.starter)
            found = len(items)
            report = render(items)
        else:
            ap.error("give a starter directory or --diff OLD_DIR NEW_DIR")
    except (FileNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.out:
        dirs = args.diff or [args.starter]
        if overwrites_input(args.out, [os.path.join(d, f) for d in dirs for f in FILES]):
            print(f"error: --out {args.out} is one of the starter files being read; refusing to overwrite it",
                  file=sys.stderr)
            return 2
        try:
            if os.path.dirname(args.out):
                os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(report + "\n")
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc.strerror}", file=sys.stderr)
            return 2
        print(f"wrote {args.out}")
    else:
        print(report)
    if not found:
        print("UNKNOWN no requirement line found; read AGENTS.md and problem_statement.md in full", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
