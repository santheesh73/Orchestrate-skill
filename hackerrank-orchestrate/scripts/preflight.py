#!/usr/bin/env python3
"""Check an Orchestrate output CSV against the contract before submitting.

Failure it prevents: whole rows lost to a wrong header, a missing or duplicate id,
or an off-enum value, regardless of how good the reasoning was.

Checks:
  - the file is UTF-8 and parses as CSV
  - the header equals the expected columns, in order (from --template or --columns)
  - one row per input id (from --inputs/--id-col): none missing, none extra, no duplicates
  - row order follows the input order (warning only)
  - each --enum column holds only allowed values
  - each --nonempty column is never blank
  - every row has the right number of fields

Nothing is hardcoded: read the columns and allowed values from this edition's
AGENTS.md / problem_statement.md and pass them in.

Examples:
  python preflight.py output.csv --template dataset/output.csv \
      --inputs dataset/requests.csv --id-col request_id \
      --enum "status=replied|escalated" --nonempty justification

Exit code 0 when clean, 1 when any error is found, 2 on usage errors, 3 when the file
has no data rows and nothing else is wrong (nothing was checked, so nothing passed).
Standard library only.
"""

import argparse
import csv
import io
import os
import stat
import sys
from collections import Counter

# A justification can exceed the csv module's 131072-character default field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    bom = raw.startswith("﻿")
    if bom:
        raw = raw[1:]
    try:
        rows = list(csv.reader(io.StringIO(raw, newline=None)))
    except csv.Error as exc:  # e.g. a NUL byte on Python 3.9
        raise ValueError(f"{path} is not parseable as CSV: {exc}") from None
    return rows, bom


def parse_enum(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"--enum must look like col=a|b|c, got {spec!r}")
    col, values = spec.split("=", 1)
    return col.strip(), set(v.strip() for v in values.split("|"))


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
    ap.add_argument("output", help="the output CSV to check")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--template", help="blank template CSV whose header is the expected column list")
    src.add_argument("--columns", help="expected columns, comma-separated, in order")
    ap.add_argument("--inputs", help="input CSV that needs one output row per id")
    ap.add_argument("--id-col", help="id column name, shared by inputs and output")
    ap.add_argument("--enum", action="append", default=[], type=parse_enum,
                    help='allowed values, e.g. "status=a|b|c" (repeatable)')
    ap.add_argument("--nonempty", action="append", default=[], help="column that must never be blank (repeatable)")
    ap.add_argument("--max-show", type=bounded_int(0), default=10, help="examples to print per problem")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2

    errors, warnings = [], []

    def problem(kind, items, label):
        items = list(items)
        if items:
            shown = ", ".join(str(i) for i in items[: args.max_show])
            more = f" (+{len(items) - args.max_show} more)" if len(items) > args.max_show else ""
            (errors if kind == "error" else warnings).append(f"{label} [{len(items)}]: {shown}{more}")

    try:
        if args.template:
            trows, _ = read_csv(args.template)
            if not trows:
                print("error: template is empty", file=sys.stderr)
                return 2
            expected = [c.strip() for c in trows[0]]
        else:
            expected = [c.strip() for c in args.columns.split(",")]
        rows, bom = read_csv(args.output)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if bom:
        warnings.append("output starts with a UTF-8 BOM; most graders accept it, but the template has none")
    if not rows:
        print("ERROR output is empty")
        return 1

    header, data = rows[0], rows[1:]
    dup_cols = sorted({c for c in header if header.count(c) > 1})
    if dup_cols:
        errors.append(f"duplicate header columns: {dup_cols}")
    if header != expected:
        if [h.strip() for h in header] == expected:
            errors.append("header has stray whitespace around column names")
        else:
            missing = [c for c in expected if c not in header]
            extra = [c for c in header if c not in expected]
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if extra:
                detail.append(f"unexpected {extra}")
            if not missing and not extra:
                detail.append("same columns, wrong order")
            errors.append(f"header mismatch: {'; '.join(detail)}\n      expected: {','.join(expected)}\n      got:      {','.join(header)}")

    col_index = {c: i for i, c in enumerate(header)}
    problem("error", (n + 2 for n, r in enumerate(data) if len(r) != len(header)),
            f"rows with a field count other than {len(header)} (line numbers)")
    data = [r for r in data if len(r) == len(header)]

    if args.id_col:
        if args.id_col not in col_index:
            errors.append(f"id column {args.id_col!r} is not in the output header")
        else:
            out_ids = [r[col_index[args.id_col]] for r in data]
            dupes = [i for i, c in Counter(out_ids).items() if c > 1]
            problem("error", dupes, "duplicate ids")
            problem("error", (n + 2 for n, i in enumerate(out_ids) if not i.strip()), "rows with a blank id (line numbers)")
            if args.inputs:
                try:
                    irows, _ = read_csv(args.inputs)
                except (OSError, ValueError) as exc:
                    print(f"error: {exc}", file=sys.stderr)
                    return 2
                if not irows or args.id_col not in irows[0]:
                    errors.append(f"id column {args.id_col!r} is not in the inputs header")
                else:
                    k = irows[0].index(args.id_col)
                    in_ids = [r[k] for r in irows[1:] if len(r) > k]
                    in_set, out_set = set(in_ids), set(out_ids)
                    problem("error", [i for i in in_ids if i not in out_set], "input ids with no output row")
                    problem("error", [i for i in out_ids if i not in in_set], "output ids not in the inputs")
                    common_in = [i for i in in_ids if i in out_set]
                    seen, common_out = set(), []
                    for i in out_ids:
                        if i in in_set and i not in seen:
                            seen.add(i)
                            common_out.append(i)
                    if common_in != common_out:
                        warnings.append("output rows are not in input order")
    elif args.inputs:
        print("error: --inputs needs --id-col", file=sys.stderr)
        return 2

    for col, allowed in args.enum:
        if col not in col_index:
            errors.append(f"--enum column {col!r} is not in the output header")
            continue
        k = col_index[col]
        bad = Counter(r[k] for r in data if r[k] not in allowed)
        problem("error", (f"{v!r} x{c}" for v, c in bad.most_common()), f"off-enum values in {col}")
        dist = Counter(r[k] for r in data)
        if data and len(dist) == 1:
            warnings.append(f"every row has the same {col} ({next(iter(dist))!r}); a collapsed distribution is usually invalid")

    for col in args.nonempty:
        if col not in col_index:
            errors.append(f"--nonempty column {col!r} is not in the output header")
            continue
        k = col_index[col]
        problem("error", (n + 2 for n, r in enumerate(data) if not r[k].strip()), f"blank {col} (line numbers)")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"{len(data)} rows checked: {len(errors)} errors, {len(warnings)} warnings")
    if errors:
        return 1
    if not data:
        print("UNKNOWN no data rows, so no row was checked")
        return 3
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
