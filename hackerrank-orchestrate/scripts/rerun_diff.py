#!/usr/bin/env python3
"""Diff two runs of an Orchestrate output CSV: churn per column and the noise floor.

Failure it prevents: shipping a change whose blast radius nobody measured, and calling
a change an improvement when it is inside the model's run-to-run noise.

Use it:
  - after any core or extraction change (blast radius on the full input set)
  - on two offline runs from the cache (should be 0 changed rows)
  - once against a cold re-derivation from the live model (your noise floor)

Modes:
  rerun_diff.py A.csv B.csv --id-col request_id
  rerun_diff.py --cmd "python code/main.py --from-cache" --output output.csv --id-col request_id
      runs the command twice, snapshotting the output after each run, then diffs

Exit code 0 when the runs are identical, 1 when any row differs, 2 on usage errors, 3 when
neither run has a data row (nothing was compared, so "identical" would mean nothing).
Standard library only.
"""

import argparse
import csv
import hashlib
import io
import os
import shlex
import shutil
import subprocess
import stat
import sys
import tempfile

# A justification can exceed the csv module's 131072-character default field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def load(path, id_col):
    with open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=None))
    try:
        fields = reader.fieldnames or []
        records = list(reader)
    except csv.Error as exc:  # e.g. a NUL byte on Python 3.9
        raise ValueError(f"{path} is not parseable as CSV: {exc}") from None
    if id_col not in fields:
        raise ValueError(f"{path} has no column {id_col!r}")
    dupes = sorted({c for c in fields if fields.count(c) > 1})
    if dupes:
        raise ValueError(f"{path} has duplicate columns {dupes}; values would be silently overwritten")
    rows = {}
    for r in records:
        if r[id_col] in rows:
            raise ValueError(f"{path} has duplicate id {r[id_col]!r}")
        rows[r[id_col]] = r
    return reader.fieldnames, rows, digest


def run_twice(cmd, output, timeout):
    snaps = []
    tmp = tempfile.mkdtemp(prefix="rerun_diff_")
    for i in (1, 2):
        print(f"run {i}: {cmd}", file=sys.stderr)
        proc = subprocess.run(shlex.split(cmd), timeout=timeout)
        if proc.returncode != 0:
            raise ValueError(f"run {i} exited with {proc.returncode}")
        if not os.path.exists(output):
            raise ValueError(f"run {i} did not produce {output}")
        dest = os.path.join(tmp, f"run{i}.csv")
        shutil.copyfile(output, dest)
        snaps.append(dest)
    return snaps


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
    ap.add_argument("files", nargs="*", help="two CSVs to compare (A then B)")
    ap.add_argument("--id-col", required=True, help="row id column")
    ap.add_argument("--cmd", help="command that writes the output; run twice and compare")
    ap.add_argument("--output", help="output path the command writes (with --cmd)")
    ap.add_argument("--timeout", type=bounded_int(1), default=3600, help="seconds per run (with --cmd)")
    ap.add_argument("--ignore", action="append", default=[],
                    help="column to exclude from the diff, e.g. a free-text explanation (repeatable)")
    ap.add_argument("--show", type=bounded_int(0), default=5, help="example ids to print per column")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2

    if args.cmd and not args.output:
        ap.error("--cmd needs --output")
    if not args.cmd and len(args.files) != 2:
        ap.error("give two CSV files, or --cmd with --output")
    try:
        a_path, b_path = run_twice(args.cmd, args.output, args.timeout) if args.cmd else args.files
        a_cols, a, a_hash = load(a_path, args.id_col)
        b_cols, b, b_hash = load(b_path, args.id_col)
    except (ValueError, OSError, UnicodeDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"A sha256 {a_hash[:16]}  rows {len(a)}")
    print(f"B sha256 {b_hash[:16]}  rows {len(b)}")
    if not a and not b:
        print("UNKNOWN neither run has a data row, so nothing was compared")
        return 3
    if a_hash == b_hash:
        print("identical bytes: 0 rows changed")
        return 0
    if a_cols != b_cols:
        print(f"WARN  column lists differ:\n      A: {a_cols}\n      B: {b_cols}")

    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    if only_a:
        print(f"ids only in A [{len(only_a)}]: {', '.join(only_a[:args.show])}")
    if only_b:
        print(f"ids only in B [{len(only_b)}]: {', '.join(only_b[:args.show])}")

    common = [i for i in a if i in b]
    cols = [c for c in a_cols if c in b_cols and c != args.id_col and c not in args.ignore]
    changed_rows = set()
    print(f"\n{'column':<40} {'changed':>8} {'of':>6}  examples")
    for c in cols:
        ids = [i for i in common if a[i][c] != b[i][c]]
        changed_rows.update(ids)
        ex = ", ".join(ids[: args.show])
        print(f"{c:<40} {len(ids):>8} {len(common):>6}  {ex}")
    n = len(common)
    pct = 100.0 * (n - len(changed_rows)) / n if n else 100.0
    print(f"\nrows changed in any compared column: {len(changed_rows)} of {n} ({pct:.1f}% stable)")
    if args.ignore:
        print(f"ignored columns: {', '.join(args.ignore)}")
    differs = bool(changed_rows or only_a or only_b)
    return 1 if differs else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
