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

Exit code 0 when the runs are identical, 1 when any row differs, 2 on usage errors.
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
import sys
import tempfile


def load(path, id_col):
    with open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if id_col not in (reader.fieldnames or []):
        raise SystemExit(f"error: {path} has no column {id_col!r}")
    rows = {}
    for r in reader:
        rows[r[id_col]] = r
    return reader.fieldnames, rows, digest


def run_twice(cmd, output, timeout):
    snaps = []
    tmp = tempfile.mkdtemp(prefix="rerun_diff_")
    for i in (1, 2):
        print(f"run {i}: {cmd}", file=sys.stderr)
        proc = subprocess.run(shlex.split(cmd), timeout=timeout)
        if proc.returncode != 0:
            raise SystemExit(f"error: run {i} exited with {proc.returncode}")
        if not os.path.exists(output):
            raise SystemExit(f"error: run {i} did not produce {output}")
        dest = os.path.join(tmp, f"run{i}.csv")
        shutil.copyfile(output, dest)
        snaps.append(dest)
    return snaps


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="two CSVs to compare (A then B)")
    ap.add_argument("--id-col", required=True, help="row id column")
    ap.add_argument("--cmd", help="command that writes the output; run twice and compare")
    ap.add_argument("--output", help="output path the command writes (with --cmd)")
    ap.add_argument("--timeout", type=int, default=3600, help="seconds per run (with --cmd)")
    ap.add_argument("--ignore", action="append", default=[],
                    help="column to exclude from the diff, e.g. a free-text explanation (repeatable)")
    ap.add_argument("--show", type=int, default=5, help="example ids to print per column")
    args = ap.parse_args(argv)

    if args.cmd:
        if not args.output:
            ap.error("--cmd needs --output")
        a_path, b_path = run_twice(args.cmd, args.output, args.timeout)
    elif len(args.files) == 2:
        a_path, b_path = args.files
    else:
        ap.error("give two CSV files, or --cmd with --output")

    a_cols, a, a_hash = load(a_path, args.id_col)
    b_cols, b, b_hash = load(b_path, args.id_col)
    print(f"A sha256 {a_hash[:16]}  rows {len(a)}")
    print(f"B sha256 {b_hash[:16]}  rows {len(b)}")
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
    sys.exit(main())
