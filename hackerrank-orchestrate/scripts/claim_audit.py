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
each one and either fix the doc or say why it differs. A claim counts as checked only
when the matching live count was available (a "rows" claim needs --csv, and so on).

Exit codes: 0 when at least one claim was checked (mismatches included, unless
--strict); 1 with --strict and any mismatch; 2 on usage errors; 3 when no claim could
be checked, because the docs make none or none matches a live count you supplied. A
check that examined nothing is not a pass.

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
import stat
import sys
import warnings

# A justification can exceed the csv module's 131072-character default field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

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
            if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")) and os.path.isfile(p):
                with open(p, encoding="utf-8-sig", errors="replace") as fh:
                    try:
                        with warnings.catch_warnings():  # invalid escapes must not hide a test file
                            warnings.simplefilter("ignore")
                            tree = ast.parse(fh.read())
                    except (SyntaxError, ValueError, RecursionError):  # ValueError: NUL byte on 3.9-3.11
                        continue
                n += sum(1 for node in ast.walk(tree)
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"))
            elif re.search(r"\.(test|spec)\.[jt]sx?$", f):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    n += len(re.findall(r"^\s*(?:it|test)\s*\(", fh.read(), re.M))
    return n


def read_utf8(path, encoding="utf-8"):
    try:
        with open(path, encoding=encoding, newline="") as fh:
            return fh.read()
    except UnicodeDecodeError:
        raise ValueError(f"{path} is not valid UTF-8") from None


def count_csv_rows(path):
    try:
        rows = list(csv.reader(io.StringIO(read_utf8(path, "utf-8-sig"), newline=None)))
    except csv.Error as exc:  # e.g. a NUL byte on Python 3.9
        raise ValueError(f"{path} is not parseable as CSV: {exc}") from None
    return max(len([r for r in rows if any(c.strip() for c in r)]) - 1, 0)


def count_constants(path):
    n = 0
    lines = [l.strip() for l in read_utf8(path).splitlines() if l.strip().startswith("|")]
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
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2

    docs = []
    for pattern in args.docs:
        docs += sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else [])
    missing = [p for p in [args.repo, args.constants] + args.csv if p and not os.path.exists(p)]
    if not docs or missing:
        print(f"error: missing {missing or 'docs'}", file=sys.stderr)
        return 2
    if args.repo and not os.path.isdir(args.repo):
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 2
    exclude = ([] if args.no_default_exclude else list(DEFAULT_EXCLUDES)) + args.exclude
    try:
        results, live = audit(docs, args.repo, args.csv, args.constants, exclude)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for status, doc, lineno, text, actual in results:
        if args.quiet and status != "MISMATCH":
            continue
        extra = "" if actual is None else f" (live: {', '.join(map(str, actual))})"
        print(f"{status:<9} {doc}:{lineno}: {text!r}{extra}")
    mism = sum(1 for r in results if r[0] == "MISMATCH")
    checked = sum(1 for r in results if r[0] in ("OK", "MISMATCH"))
    counted = ", ".join(f"{k}s={'/'.join(map(str, v))}" for k, v in live.items()) or "nothing"
    print(f"{len(results)} claims, {checked} checked, {mism} mismatches (hints, not proof); live counts: {counted}")
    if not checked:
        return 3
    return 1 if (args.strict and mism) else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
