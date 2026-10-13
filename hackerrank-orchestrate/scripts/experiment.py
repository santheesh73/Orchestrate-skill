#!/usr/bin/env python3
"""Run one change-record experiment: baseline, re-run, full-set diff, verdict.

Failure it prevents: a change shipped on a verdict worked out by hand. By hand, the
labeled better/worse counts get miscounted, the one-row and mixed cases of the
resolution table get read two ways (net gain versus rows made worse), the noise floor
is forgotten, and the blast radius is measured on one column instead of every input.

  experiment.py start NAME --output output.csv --id-col request_id \
      --cmd "python code/main.py --from-cache" --check "python -m pytest -q" \
      --labels dataset/output.csv --ignore justification --noise-floor 1
  (make the change)
  experiment.py finish NAME --change "escalate bypass requests" \
      --requirement "rule 3 of problem_statement.md" --record docs/changes.md
  experiment.py list

start  runs --cmd (optional; without it the current --output is the baseline), copies
       --output, and runs every --check. Settings are stored, so finish repeats the
       same evaluation.
finish runs --cmd and the checks again, diffs every row of the FULL output (not only
       the column you meant to change), counts labeled rows made better and worse
       against --labels, applies the resolution table in references/evaluation.md and
       appends a change record (assets/change_record.md fields) to --record.
list   shows every experiment and its verdict.

The verdict, computed by resolve():
  UNKNOWN  no label-free check was run, or no labeled row could be compared
  REJECT   a label-free check fails at finish (it regressed, or it was already red: a
           hard gate), or 2+ labeled rows got worse that --accounts-for does not
           explain (hard rule 4)
  NOISE    net labeled gain (better - worse) at most max(1, noise floor): keep the
           change only if its written reason holds; never call it an improvement
  SHIP     net gain of 2+ rows and above the noise floor; check the blast radius
A one-row difference is never SHIP. A noise floor that was not measured is UNKNOWN and
the table's minimum (1 row) is used, which the output says.

It never edits your code, data or output: it reads --output and writes only under
--dir (default .experiments) and to --record. Exit 0 SHIP, 1 REJECT, 2 usage errors
(bad name, missing file, unparsable CSV, a command that fails), 3 UNKNOWN, 4 NOISE.
Standard library only; no network.
"""

import argparse
import csv
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import stat
import sys
import time

# A justification can exceed the csv module's 131072-character default field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
EXIT = {"SHIP": 0, "REJECT": 1, "UNKNOWN": 3, "NOISE": 4}
TABLE_MIN_FLOOR = 1  # evaluation.md: "Never accept or reject on a one-row difference"


class UsageError(Exception):
    pass


def load_rows(path, id_col):
    """Rows of a CSV keyed by id. Raises UsageError on anything unusable."""
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=None))
        fields = reader.fieldnames or []
        records = list(reader)
    except OSError as exc:
        raise UsageError(f"cannot read {path}: {exc.strerror or exc}")
    except UnicodeDecodeError:
        raise UsageError(f"{path} is not UTF-8")
    except csv.Error as exc:  # e.g. a NUL byte on Python 3.9
        raise UsageError(f"{path} is not parseable as CSV: {exc}")
    if id_col not in fields:
        raise UsageError(f"{path} has no column {id_col!r}")
    dupes = sorted({c for c in fields if fields.count(c) > 1})
    if dupes:
        raise UsageError(f"{path} has duplicate columns {dupes}")
    rows = {}
    for n, r in enumerate(records, 2):
        if None in r or None in r.values():
            raise UsageError(f"{path} row {n} has {'more' if None in r else 'fewer'} fields than the header")
        key = r.get(id_col) or ""
        if key in rows:
            raise UsageError(f"{path} has duplicate id {key!r}")
        rows[key] = {k: (v if v is not None else "") for k, v in r.items() if k is not None}
    return fields, rows


def run_cmd(cmd, timeout):
    if not cmd:
        return
    try:
        proc = subprocess.run(shlex.split(cmd), timeout=timeout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise UsageError(f"--cmd could not run: {exc}")
    if proc.returncode != 0:
        raise UsageError(f"--cmd exited with {proc.returncode}: {cmd}")


def run_checks(checks, timeout):
    """Exit code of each label-free check command (None when it could not start)."""
    results = []
    for c in checks:
        try:
            rc = subprocess.run(shlex.split(c), timeout=timeout, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).returncode
        except (OSError, ValueError, subprocess.TimeoutExpired):
            rc = None
        results.append(rc)
    return results


def resolve(checks_before, checks_after, labeled, better, worse, accounted, noise_floor):
    """The resolution table of references/evaluation.md as one function: (verdict, reason)."""
    if not checks_after:
        return "UNKNOWN", "no label-free check was run, so the first column of the table is unknown"
    regressed = [i for i, (b, a) in enumerate(zip(checks_before, checks_after), 1) if b == 0 and a != 0]
    if regressed:
        return "REJECT", f"label-free check {', '.join(map(str, regressed))} passed before and fails now"
    failing = [i for i, a in enumerate(checks_after, 1) if a != 0]
    if failing:  # a hard gate (evaluation.md section 6) blocks the merge even when it was already red
        return "REJECT", f"label-free check {', '.join(map(str, failing))} fails before and after; fix it first"
    if labeled == 0:
        return "UNKNOWN", "no labeled row could be compared, so the labeled column of the table is unknown"
    unexplained = [w for w in worse if w not in set(accounted)]
    if len(unexplained) >= 2:
        return "REJECT", (f"{len(worse)} labeled rows got worse and the written reason does not explain "
                          f"{', '.join(unexplained)}")
    floor = max(TABLE_MIN_FLOOR, noise_floor if noise_floor is not None else TABLE_MIN_FLOOR)
    net = len(better) - len(worse)
    if net > floor:
        return "SHIP", f"net gain {net:+d} labeled rows is above the noise floor of {floor}; check the blast radius"
    return "NOISE", (f"net gain {net:+d} labeled rows is within the noise floor of {floor}; keep the change "
                     "only if its written reason holds, and do not call it an improvement")


def compare(before, after, id_col, ignore):
    cols = [c for c in before[0] if c in after[0] and c != id_col and c not in ignore]
    a, b = before[1], after[1]
    changed = sorted(i for i in set(a) | set(b) if i not in a or i not in b or any(a[i][c] != b[i][c] for c in cols))
    return changed, len(set(a) | set(b))


def label_outcome(rows, labels, id_col, label_cols):
    """Ids of labeled rows the output gets right."""
    return {i for i, lab in labels.items()
            if i in rows and all(rows[i].get(c, "").strip() == lab.get(c, "").strip() for c in label_cols)}


def exp_dir(base, name):
    if not NAME_RE.fullmatch(name or ""):
        raise UsageError(f"experiment name {name!r} must be letters, digits, '.', '_' or '-' (at most 64)")
    return os.path.join(base, name)


META_TYPES = {"name": str, "status": str, "output": str, "id_col": str, "cmd": (str, type(None)),
              "timeout": int, "checks": list, "checks_before": list, "labels": (str, type(None)),
              "label_cols": list, "ignore": list, "noise_floor": (int, type(None))}


def load_meta(path):
    """meta.json as start wrote it; a hand-edited or damaged file is a usage error, not a traceback."""
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError, RecursionError) as exc:
        raise UsageError(f"cannot read {path}: {exc.__class__.__name__}")
    bad = [k for k, t in META_TYPES.items() if not isinstance(m, dict) or not isinstance(m.get(k), t)
           or isinstance(m.get(k), bool)] if isinstance(m, dict) else ["(not a JSON object)"]
    if not bad:
        lists = (m["checks"], m["label_cols"], m["ignore"])
        if not all(isinstance(x, str) for l in lists for x in l) or \
                not all(x is None or (isinstance(x, int) and not isinstance(x, bool)) for x in m["checks_before"]):
            bad = ["checks / label_cols / ignore / checks_before entries"]
    if bad:
        raise UsageError(f"{path} is damaged ({', '.join(bad)}); start a new experiment")
    return m


def same_place(a, b):
    """Two paths name one file, by resolved path (works before either exists) or by inode."""
    if os.path.realpath(a) == os.path.realpath(b):
        return True
    return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)


def copy_into(src, dest):
    """Copy beside dest, then rename over it: a symlink planted at dest is replaced, never followed."""
    tmp = dest + ".tmp"
    if os.path.lexists(tmp):
        os.unlink(tmp)
    shutil.copyfile(src, tmp)
    os.replace(tmp, dest)


def save_meta(path, meta):
    tmp = path + ".tmp"
    if os.path.lexists(tmp):
        os.unlink(tmp)
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    os.replace(tmp, path)


def cmd_start(a):
    d = exp_dir(a.dir, a.name)
    if os.path.lexists(d):
        raise UsageError(f"experiment {a.name!r} already exists in {a.dir}")
    labels, label_cols = None, []
    if a.labels:
        lf, _ = load_rows(a.labels, a.id_col)
        label_cols = a.label_col or [c for c in lf if c != a.id_col and c not in a.ignore]
        missing = [c for c in label_cols if c not in lf]
        if missing or not label_cols:
            raise UsageError(f"--labels has no column(s) {missing or 'to compare'}")
        if same_place(a.labels, a.output):
            raise UsageError("--labels is the --output file; every changed row would count as better")
        labels = a.labels
    run_cmd(a.cmd, a.timeout)
    load_rows(a.output, a.id_col)  # validate before storing anything
    checks = run_checks(a.check, a.timeout)
    broken = [c for c, rc in zip(a.check, checks) if rc is None]
    if broken:  # a check that cannot start would read as a failing gate at finish
        raise UsageError(f"--check could not start or timed out: {broken[0]}")
    try:
        os.makedirs(d)  # fails if another start took the name meanwhile; never remove its folder
    except OSError as exc:
        raise UsageError(f"cannot create {d}: {exc.strerror or exc}")
    try:
        copy_into(a.output, os.path.join(d, "baseline.csv"))
    except OSError as exc:
        shutil.rmtree(d, ignore_errors=True)
        raise UsageError(f"cannot write {d}: {exc.strerror or exc}")
    save_meta(os.path.join(d, "meta.json"), {
        "name": a.name, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "started",
        "output": os.path.abspath(a.output), "id_col": a.id_col, "cmd": a.cmd, "timeout": a.timeout,
        "checks": a.check, "checks_before": checks, "labels": os.path.abspath(labels) if labels else None,
        "label_cols": label_cols, "ignore": a.ignore, "noise_floor": a.noise_floor})
    print(f"started {a.name}: baseline {a.output} stored; checks {fmt_checks(a.check, checks)}")
    return 0


def fmt_checks(checks, rcs):
    if not checks:
        return "none (the verdict will be UNKNOWN)"
    return ", ".join(f"{i}:{'pass' if rc == 0 else 'FAIL'}" for i, rc in enumerate(rcs, 1))


def cmd_finish(a):
    d = exp_dir(a.dir, a.name)
    if not os.path.isfile(os.path.join(d, "meta.json")):
        raise UsageError(f"no experiment {a.name!r} in {a.dir}")
    m = load_meta(os.path.join(d, "meta.json"))
    if m.get("status") != "started":
        raise UsageError(f"experiment {a.name!r} already finished ({m.get('status')}); start a new one")
    record = a.record or os.path.join(a.dir, "changes.md")
    check_record(record, m, a.dir)
    run_cmd(m["cmd"], m["timeout"])
    check_record(record, m, a.dir)  # the command may have created the output since
    before = load_rows(os.path.join(d, "baseline.csv"), m["id_col"])
    after = load_rows(m["output"], m["id_col"])
    try:
        copy_into(m["output"], os.path.join(d, "after.csv"))
    except OSError as exc:
        raise UsageError(f"cannot write {d}: {exc.strerror or exc}")
    checks_after = run_checks(m["checks"], m["timeout"])
    changed, total = compare(before, after, m["id_col"], m["ignore"])

    better, worse, labeled = [], [], 0
    if m["labels"]:
        _, labels = load_rows(m["labels"], m["id_col"])
        common = {i: v for i, v in labels.items() if i in before[1] and i in after[1]}
        labeled = len(common)
        right_b = label_outcome(before[1], common, m["id_col"], m["label_cols"])
        right_a = label_outcome(after[1], common, m["id_col"], m["label_cols"])
        better, worse = sorted(right_a - right_b), sorted(right_b - right_a)
        right_counts = (len(right_b), len(right_a))
    verdict, reason = resolve(m["checks_before"], checks_after, labeled, better, worse, a.accounts_for,
                              m["noise_floor"])
    floor = "UNKNOWN (not measured; the table minimum of 1 row is used)" if m["noise_floor"] is None \
        else f"{m['noise_floor']} rows"
    lines = [
        f"blast radius: {len(changed)} of {total} rows changed in any compared column (full output)",
        f"label-free checks: before {fmt_checks(m['checks'], m['checks_before'])}; "
        f"after {fmt_checks(m['checks'], checks_after)}",
        (f"labeled rows: {labeled}; right before {right_counts[0]}, after {right_counts[1]}; "
         f"better {len(better)} {better[:10]}, worse {len(worse)} {worse[:10]}") if labeled else
        "labeled rows: none compared (no --labels at start, or no labeled id in both runs)",
        f"noise floor: {floor}",
        f"VERDICT: {verdict}: {reason}",
    ]
    print("\n".join(lines))
    block = change_record(a, m, lines, changed, total, labeled, better, worse, verdict, reason)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(record)), exist_ok=True)
        with open(record, "a", encoding="utf-8") as fh:
            fh.write(block)
    except OSError as exc:
        raise UsageError(f"cannot append the change record to {record}: {exc.strerror or exc}")
    m.update(status=verdict, reason=reason, finished=time.strftime("%Y-%m-%dT%H:%M:%S"),
             checks_after=checks_after, changed=len(changed), better=better, worse=worse,
             accounts_for=a.accounts_for)
    save_meta(os.path.join(d, "meta.json"), m)
    print(f"change record appended to {record}")
    return EXIT[verdict]


def check_record(record, m, base):
    """The record never lands on the experiment's inputs or inside any experiment's folder."""
    for kept in (m["output"], m["labels"]):
        if kept and same_place(record, kept):
            raise UsageError(f"--record {record} is the experiment's own input; appending would corrupt it")
    try:
        inside = os.path.relpath(os.path.realpath(record), os.path.realpath(base))
    except ValueError:  # another drive on Windows
        return
    if not inside.startswith(os.pardir) and os.sep in inside:
        raise UsageError(f"--record {record} is inside an experiment folder; it would be overwritten or corrupt it")


def change_record(a, m, lines, changed, total, labeled, better, worse, verdict, reason):
    fill = "(fill in)"
    return "\n".join([
        "", "```",
        f"CHANGE:          {a.change or m['name']}",
        f"REQUIREMENT:     {a.requirement or fill}",
        f"CEILING:         {a.ceiling or fill}",
        f"CLAIM:           {a.claim or fill}",
        f"JUSTIFICATION:   {a.justification or fill}",
        f"METRIC:          label-free checks: {len(m['checks'])}; labeled rows compared: {labeled} "
        f"(columns {', '.join(m['label_cols']) or 'none'})",
        f"BASELINE:        {lines[1].split('; after')[0]}",
        f"RESULT:          {lines[2]}",
        f"BLAST RADIUS:    {len(changed)} of {total} rows changed on the FULL output; "
        f"right direction {len(better)}; wrong direction {len(worse)}",
        f"COUNTERFACTUAL:  {a.counterfactual or fill}",
        f"VERDICT:         {verdict} ({reason}); experiment {m['name']}",
        "```", ""])


def cmd_list(a):
    if not os.path.isdir(a.dir):
        print(f"no experiments in {a.dir}")
        return 0
    names = sorted(n for n in os.listdir(a.dir) if os.path.isfile(os.path.join(a.dir, n, "meta.json")))
    for n in names:
        try:
            m = load_meta(os.path.join(a.dir, n, "meta.json"))
            print(f"{n:<32} {m['status']:<8} started {m.get('started', '?')}  {m.get('reason', '')}")
        except UsageError:
            print(f"{n:<32} damaged meta.json")
    print(f"{len(names)} experiments in {a.dir}")
    return 0


def bounded_int(low):
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
    ap.add_argument("--dir", default=".experiments", help="where experiments are stored (default .experiments)")
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("start", help="store the baseline")
    s.add_argument("name")
    s.add_argument("--output", required=True, help="the output CSV your pipeline writes")
    s.add_argument("--id-col", required=True, help="row id column")
    s.add_argument("--cmd", help="command that writes --output (run at start and at finish)")
    s.add_argument("--check", action="append", default=[], help="label-free check command; exit 0 = pass (repeatable)")
    s.add_argument("--labels", help="CSV of labeled rows (for example the sample rows), keyed by --id-col")
    s.add_argument("--label-col", action="append", default=[], help="column to compare with the labels (default: all)")
    s.add_argument("--ignore", action="append", default=[], help="column left out of diffs, e.g. free text (repeatable)")
    s.add_argument("--noise-floor", type=bounded_int(0), help="rows that change between two cold runs (rerun_diff.py)")
    s.add_argument("--timeout", type=bounded_int(1), default=3600, help="seconds per command")
    f = sub.add_parser("finish", help="re-run, diff, and decide")
    f.add_argument("name")
    f.add_argument("--accounts-for", action="append", default=[], metavar="ID",
                   help="a worse labeled row the change's written reason explains (repeatable)")
    f.add_argument("--record", help="file to append the change record to (default DIR/changes.md)")
    for field in ("change", "requirement", "ceiling", "claim", "justification", "counterfactual"):
        f.add_argument("--" + field, help=f"text for the {field.upper()} line of the change record")
    sub.add_parser("list", help="list experiments")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2
    try:
        return {"start": cmd_start, "finish": cmd_finish, "list": cmd_list}[args.command](args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
