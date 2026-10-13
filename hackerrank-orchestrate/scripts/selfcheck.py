#!/usr/bin/env python3
"""Gate 7 in one command: run every bundled check from one JSON config.

Failure it prevents: skipping part of the self-score under deadline pressure because
it needs six separate commands, or reading a skipped check as a pass.

Checks (each section of the config is optional):
  starter         hard rule 1: AGENTS.md matches the sha256 recorded at kickoff, and
                  CLAUDE.md (if configured) still holds the line @AGENTS.md
  log             check_log.py on log.txt
  output          preflight.py on output.csv
  usage_report    the usage report exists and names calls, tokens and cost
  constants       interview_drill.py: named constants missing from CONSTANTS.md
  corpus_literals corpus_literals.py: code literals copied from the dataset
  claims          claim_audit.py: numbers in docs versus the live repo (hints only)

A section missing from the config prints UNKNOWN, never PASS, and so does any section
that examined nothing: an output with no data rows, a constants scan that found no
source file or no named constant, a corpus_literals scan with no source file or no
dataset value, and claims whose docs make nothing checkable (each script's exit 3). A
configured file that does not exist is FAIL. Results: PASS, WARN, UNKNOWN, FAIL. The exit code is the worst
result: 0 PASS, 1 WARN, 2 UNKNOWN, 3 FAIL; 4 means the config itself is unusable.
Paths in the config are relative to the config file's directory, except claims.exclude,
which is relative to claims.repo and adds to claim_audit's default (tests/fixtures).

Example config (selfcheck.json):
  {
    "starter": {"agents_md": "AGENTS.md", "sha256": "<printed by the first run>",
                "claude_md": "CLAUDE.md"},
    "log": {"path": "log.txt", "expect_tool": "Claude Code", "profile": "sept-2026"},
    "output": {"path": "output.csv", "template": "dataset/output.csv",
               "inputs": "dataset/requests.csv", "id_col": "request_id",
               "enums": {"status": ["replied", "escalated"]}, "nonempty": ["justification"]},
    "usage_report": {"path": "code/evaluation/usage_report.md"},
    "constants": {"code": ["code"], "constants": "CONSTANTS.md"},
    "corpus_literals": {"data": ["dataset/*.csv"], "code": ["code"],
                        "spec": ["problem_statement.md", "AGENTS.md"]},
    "claims": {"docs": ["code/README.md", "CONSTANTS.md"], "repo": ".",
               "csv": ["output.csv"], "constants": "CONSTANTS.md",
               "exclude": ["code/vendor"]}
  }

These scripts check the participant's work; they are not part of the submission.
Standard library only.
"""

import argparse
import contextlib
import glob
import hashlib
import io
import json
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_log  # noqa: E402
import claim_audit  # noqa: E402
import corpus_literals  # noqa: E402
import interview_drill  # noqa: E402
import preflight  # noqa: E402

ORDER = ["PASS", "WARN", "UNKNOWN", "FAIL"]
USAGE_TERMS = ("call", "token", "cost")


def capture(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = fn(argv)
        except SystemExit as exc:  # argparse errors
            rc = exc.code if isinstance(exc.code, int) else 2
    return rc, out.getvalue() + err.getvalue()


def last_line(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[-1] if lines else ""


class Runner:
    def __init__(self, cfg, base):
        self.cfg, self.base = cfg, base

    def p(self, path):
        if "\\" in path and not os.path.exists(os.path.join(self.base, path)):
            path = path.replace("\\", "/")  # a config written on Windows
        return path if os.path.isabs(path) else os.path.join(self.base, path)

    def missing(self, *paths):
        """Configured paths that match nothing, or only named pipes (reading one hangs)."""
        return [x for x in paths if x and not [m for m in glob.glob(self.p(x)) if not stat.S_ISFIFO(os.stat(m).st_mode)]]

    def starter(self, c):
        agents, claude = c.get("agents_md"), c.get("claude_md")
        miss = self.missing(agents, claude)
        if miss or not agents:
            return "FAIL", f"missing: {miss or 'agents_md'}", ""
        if claude:
            with open(self.p(claude), encoding="utf-8", errors="replace") as fh:
                if "@AGENTS.md" not in [l.strip() for l in fh.read().splitlines()]:
                    return "FAIL", f"{os.path.basename(claude)} no longer holds the line @AGENTS.md", ""
        with open(self.p(agents), "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        want = (c.get("sha256") or "").strip().lower()
        if not want:
            return "UNKNOWN", f"no sha256 recorded; AGENTS.md is {actual} now: record that at kickoff", ""
        if actual != want:
            return "FAIL", f"AGENTS.md changed since kickoff (sha256 {actual[:12]}, recorded {want[:12]})", ""
        return "PASS", "AGENTS.md unchanged since kickoff" + ("; CLAUDE.md imports @AGENTS.md" if claude else ""), ""

    def log(self, c):
        if self.missing(c.get("path")) or "path" not in c:
            return "FAIL", f"log not found: {c.get('path')}", ""
        argv = [self.p(c["path"])]
        if c.get("expect_tool"):
            argv += ["--expect-tool", c["expect_tool"]]
        if c.get("profile"):
            prof = c["profile"]
            argv += ["--profile", self.p(prof) if prof.endswith(".json") else prof]
        rc, out = capture(check_log.main, argv)
        return ("PASS" if rc == 0 else "FAIL"), last_line(out), out

    def output(self, c):
        need = [c.get("path"), c.get("template"), c.get("inputs")]
        miss = self.missing(*need)
        if miss or not c.get("path") or not (c.get("template") or c.get("columns")):
            return "FAIL", f"missing: {miss or 'path and template/columns'}", ""
        argv = [self.p(c["path"])]
        argv += ["--template", self.p(c["template"])] if c.get("template") else ["--columns", ",".join(c["columns"])]
        if c.get("inputs"):
            argv += ["--inputs", self.p(c["inputs"]), "--id-col", c.get("id_col", "")]
        elif c.get("id_col"):
            argv += ["--id-col", c["id_col"]]
        for col, vals in (c.get("enums") or {}).items():
            argv += ["--enum", f"{col}={'|'.join(vals)}"]
        for col in c.get("nonempty") or []:
            argv += ["--nonempty", col]
        rc, out = capture(preflight.main, argv)
        if rc == 3:  # no data rows, so nothing passed
            return "UNKNOWN", last_line(out), out
        return ("PASS" if rc == 0 else "FAIL"), last_line(out), out

    def usage_report(self, c):
        path = c.get("path")
        if not path or self.missing(path):
            return "FAIL", f"usage report not found: {path}", ""
        with open(self.p(path), encoding="utf-8") as fh:
            text = fh.read().lower()
        absent = [t for t in USAGE_TERMS if t not in text]
        if absent:
            return "FAIL", f"report does not mention: {', '.join(absent)}", ""
        return "PASS", "exists and names calls, tokens and cost", ""

    def constants(self, c):
        code, doc = c.get("code") or [], c.get("constants")
        miss = self.missing(*code, doc)
        if miss or not code or not doc:
            return "FAIL", f"missing: {miss or 'code and constants'}", ""
        stats = {}
        _, names = interview_drill.scan_paths([self.p(x) for x in code], stats=stats)
        with open(self.p(doc), encoding="utf-8") as fh:
            gone = interview_drill.missing_constants(names, fh.read())
        if gone:
            return "FAIL", f"{len(gone)} constants missing from {os.path.basename(doc)}: {', '.join(gone[:5])}", ""
        if not stats["files"] or not names:
            return "UNKNOWN", f"{stats['files']} source files, {len(set(names))} named constants: nothing to compare", ""
        return "PASS", f"{len(set(names))} named constants all documented", ""

    def corpus_literals(self, c):
        data, code = c.get("data") or [], c.get("code") or []
        miss = self.missing(*data, *code, *(c.get("spec") or []), c.get("allowlist"))
        if miss or not data or not code:
            return "FAIL", f"missing: {miss or 'data and code'}", ""
        argv = ["--data"] + [self.p(x) for x in data] + ["--code"] + [self.p(x) for x in code]
        if c.get("spec"):
            argv += ["--spec"] + [self.p(x) for x in c["spec"]]
        if c.get("allowlist"):
            argv += ["--allowlist", self.p(c["allowlist"])]
        if c.get("min_length"):
            argv += ["--min-length", str(c["min_length"])]
        rc, out = capture(corpus_literals.main, argv)
        if rc == 3:  # no source file or no dataset value was examined
            return "UNKNOWN", last_line(out), out
        return ("PASS" if rc == 0 else "FAIL"), last_line(out), out

    def claims(self, c):
        docs = c.get("docs") or []
        miss = self.missing(*docs, c.get("repo"), c.get("constants"), *(c.get("csv") or []))
        if miss or not docs:
            return "FAIL", f"missing: {miss or 'docs'}", ""
        argv = [self.p(x) for x in docs] + ["--quiet"]
        if c.get("repo"):
            argv += ["--repo", self.p(c["repo"])]
        if c.get("csv"):
            argv += ["--csv"] + [self.p(x) for x in c["csv"]]
        if c.get("constants"):
            argv += ["--constants", self.p(c["constants"])]
        for x in c.get("exclude") or []:
            argv += ["--exclude", x]
        rc, out = capture(claim_audit.main, argv)
        if rc == 3:  # nothing was checked, so nothing passed
            return "UNKNOWN", last_line(out), out
        if rc not in (0, 1):
            return "FAIL", last_line(out), out
        return ("WARN" if "MISMATCH" in out else "PASS"), last_line(out), out


CHECKS = ["starter", "log", "output", "usage_report", "constants", "corpus_literals", "claims"]


def run(cfg, base):
    r = Runner(cfg, base)
    results = []
    for name in CHECKS:
        section = cfg.get(name)
        if section is None:
            results.append((name, "UNKNOWN", "not configured, so not checked", ""))
            continue
        try:
            status, summary, detail = getattr(r, name)(section)
        except (OSError, UnicodeDecodeError, ValueError, TypeError) as exc:
            status, summary, detail = "FAIL", f"error: {exc}", ""
        results.append((name, status, summary, detail))
    return results


LIST_FIELDS = ("docs", "csv", "code", "data", "spec", "nonempty", "columns", "exclude")


def shape_errors(cfg):
    """Return config-shape problems; a wrong shape would otherwise crash or be iterated per character."""
    errs = []
    for name, sec in cfg.items():
        if not isinstance(sec, dict):
            errs.append(f"section '{name}' must be a JSON object")
            continue
        for key, val in sec.items():
            if key in LIST_FIELDS:
                if not (isinstance(val, list) and all(isinstance(x, str) for x in val)):
                    errs.append(f"{name}.{key} must be a list of strings")
            elif key == "enums":
                if not (isinstance(val, dict) and all(isinstance(v, list) and all(isinstance(x, str) for x in v)
                                                      for v in val.values())):
                    errs.append(f"{name}.enums must map column names to lists of strings")
            elif key == "min_length":
                if not isinstance(val, int) or isinstance(val, bool):
                    errs.append(f"{name}.min_length must be an integer")
            elif not isinstance(val, str):
                errs.append(f"{name}.{key} must be a string")
    return errs


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
    ap.add_argument("config", help="selfcheck JSON config")
    ap.add_argument("--verbose", action="store_true", help="print each check's full output")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2
    try:
        with open(args.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
        if not isinstance(cfg, dict):
            raise ValueError("config must be a JSON object")
    except (OSError, ValueError, RecursionError) as exc:  # RecursionError: JSON nested too deeply
        print(f"error: {exc}", file=sys.stderr)
        return 4
    unknown = set(cfg) - set(CHECKS)
    if unknown:
        print(f"error: unknown config sections {sorted(unknown)}; expected {CHECKS}", file=sys.stderr)
        return 4
    errs = shape_errors(cfg)
    for e in errs:
        print(f"error: {e}", file=sys.stderr)
    if errs:
        return 4
    results = run(cfg, os.path.dirname(os.path.abspath(args.config)))
    width = max(len(n) for n in CHECKS)
    print(f"{'check':<{width}}  {'result':<7}  summary")
    print(f"{'-' * width}  {'-' * 7}  {'-' * 40}")
    for name, status, summary, detail in results:
        print(f"{name:<{width}}  {status:<7}  {summary}")
        if args.verbose and detail.strip():
            print("    " + detail.strip().replace("\n", "\n    "))
    worst = max(ORDER.index(s) for _, s, _, _ in results)
    print(f"\nworst result: {ORDER[worst]}")
    return worst


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
