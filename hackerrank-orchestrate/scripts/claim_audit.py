#!/usr/bin/env python3
"""Compare numbers claimed in docs with the live repo.

Failure it prevents: reciting a stale number in the interview or the README ("202
tests" when 198 exist), which the judge can check against the code.

It scans the given docs for claims like "N tests", "N rows", "N constants" and
"N requests", then compares them with what it can count:
  - tests: functions named test_* in test_*.py / *_test.py files under --repo
    (counted with ast, nothing is executed), plus it/test( calls in *.test.js/ts files.
    Paths under tests/fixtures are skipped by default, because fixture projects carry
    their own tests that the real suite never runs. --exclude adds paths (relative to
    --repo, globs allowed); --no-default-exclude counts tests/fixtures too.
  - rows / requests: data-row counts of the --csv files (a claim matches if it equals
    any of them)
  - constants: data rows in the CONSTANTS.md table (--constants)

Mismatches are HINTS, never proof: a doc may describe another set on purpose. Read
each one and either fix the doc or say why it differs. Exit 0 unless --strict is set,
in which case any mismatch exits 1. Exit 2 on usage errors.

Example:
  python claim_audit.py README.md CONSTANTS.md docs/*.md --repo . \
      --csv dataset/requests.csv output.csv --constants CONSTANTS.md

Standard library only.
"""

import argparse
import ast
import csv
import fnmatch
import glob
import io
import os
import re
import sys

CLAIM_RE = re.compile(r"\b(\d[\d,]*)\s+(?:unit\s+|passing\s+|labeled\s+|sample\s+|input\s+|output\s+)?"
                      r"(tests?|rows?|constants?|requests?)\b", re.I)
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}
DEFAULT_EXCLUDES = ("tests/fixtures",)


def excluded(rel, patterns):
    rel = rel.replace(os.sep, "/")
    for pat in patterns:
        pat = pat.replace(os.sep, "/").strip("/")
        if rel == pat or rel.startswith(pat + "/") or fnmatch.fnmatch(rel, pat):
            return True
    return False


def count_tests(repo, exclude=DEFAULT_EXCLUDES):
    n = 0
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
                       and not excluded(os.path.relpath(os.path.join(dirpath, d), repo), exclude)]
        for f in filenames:
            p = os.path.join(dirpath, f)
            if excluded(os.path.relpath(p, repo), exclude):
                continue
            if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                with open(p, encoding="utf-8-sig", errors="replace") as fh:
                    try:
                        tree = ast.parse(fh.read())
                    except SyntaxError:
                        continue
                n += sum(1 for node in ast.walk(tree)
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"))
            elif re.search(r"\.(test|spec)\.[jt]sx?$", f):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    n += len(re.findall(r"^\s*(?:it|test)\s*\(", fh.read(), re.M))
    return n


def count_csv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(io.StringIO(fh.read())))
    return max(len([r for r in rows if any(c.strip() for c in r)]) - 1, 0)


def count_constants(path):
    n = 0
    with open(path, encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip().startswith("|")]
    for l in lines[2:]:  # skip header and separator
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells and cells[0] and not set(cells[0]) <= set("-: "):
            n += 1
    return n


def find_claims(path):
    claims = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            for m in CLAIM_RE.finditer(line):
                kind = m.group(2).lower().rstrip("s")
                claims.append((lineno, int(m.group(1).replace(",", "")), kind, m.group(0)))
    return claims


def audit(docs, repo=None, csvs=(), constants=None, exclude=DEFAULT_EXCLUDES):
    live = {}
    if repo:
        live["test"] = [count_tests(repo, exclude)]
    if csvs:
        live["row"] = live["request"] = [count_csv_rows(c) for c in csvs]
    if constants:
        live["constant"] = [count_constants(constants)]
    results = []
    for doc in docs:
        for lineno, n, kind, text in find_claims(doc):
            if kind not in live:
                results.append(("UNCHECKED", doc, lineno, text, None))
            elif n in live[kind]:
                results.append(("OK", doc, lineno, text, live[kind]))
            else:
                results.append(("MISMATCH", doc, lineno, text, live[kind]))
    return results, live


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+", help="Markdown or text files to scan (globs allowed)")
    ap.add_argument("--repo", help="repo root to count tests in")
    ap.add_argument("--csv", nargs="*", default=[], help="CSV files whose row counts claims may refer to")
    ap.add_argument("--constants", help="CONSTANTS.md to count table rows in")
    ap.add_argument("--exclude", action="append", default=[],
                    help="path under --repo to skip when counting tests (repeatable, globs allowed)")
    ap.add_argument("--no-default-exclude", action="store_true",
                    help=f"also count tests under {', '.join(DEFAULT_EXCLUDES)}")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any mismatch")
    ap.add_argument("--quiet", action="store_true", help="print only mismatches and the summary")
    args = ap.parse_args(argv)

    docs = []
    for pattern in args.docs:
        docs += sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else [])
    missing = [p for p in [args.repo, args.constants] + args.csv if p and not os.path.exists(p)]
    if not docs or missing:
        print(f"error: missing {missing or 'docs'}", file=sys.stderr)
        return 2
    exclude = ([] if args.no_default_exclude else list(DEFAULT_EXCLUDES)) + args.exclude
    results, live = audit(docs, args.repo, args.csv, args.constants, exclude)
    for status, doc, lineno, text, actual in results:
        if args.quiet and status != "MISMATCH":
            continue
        extra = "" if actual is None else f" (live: {', '.join(map(str, actual))})"
        print(f"{status:<9} {doc}:{lineno}: {text!r}{extra}")
    mism = sum(1 for r in results if r[0] == "MISMATCH")
    counted = ", ".join(f"{k}s={'/'.join(map(str, v))}" for k, v in live.items()) or "nothing"
    print(f"{len(results)} claims, {mism} mismatches (hints, not proof); live counts: {counted}")
    return 1 if (args.strict and mism) else 0


if __name__ == "__main__":
    sys.exit(main())
