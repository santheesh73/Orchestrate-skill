"""Standing hostile-input matrix: every script and tool, run as a subprocess, on every bad input.

Failure it prevents: the next crash on odd input. Each fixed bug in v2.2.0 had its own
test, but nothing tried every input class against every CLI. Here two things must hold
for every pair: the output never contains "Traceback", and the exit code is one the
script documents. Adding an input class or an invocation is one line in INPUTS or CASES.
"""

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SCRIPTS = os.path.join(ROOT, "hackerrank-orchestrate", "scripts")
TOOLS = os.path.join(ROOT, "tools")
SKILL = os.path.join(ROOT, "hackerrank-orchestrate")
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def _symlink(d, name, target):
    p = os.path.join(d, name)
    try:
        os.symlink(target, p)
    except (OSError, NotImplementedError):
        return None
    return p


def _loop(d):
    a, b = os.path.join(d, "loop_a"), os.path.join(d, "loop_b")
    try:
        os.symlink(b, a)
        os.symlink(a, b)
    except (OSError, NotImplementedError):
        return None
    return a


def _unreadable(d):
    if IS_ROOT or os.name == "nt":
        return None  # root reads anything; chmod 000 proves nothing there
    p = _write(os.path.join(d, "unreadable.csv"), "id,status\n1,ok\n")
    os.chmod(p, 0)
    return p


# name -> builder(tmpdir) returning a path, or None when the platform cannot make it.
INPUTS = {
    "binary": lambda d: _write(os.path.join(d, "binary.bin"), bytes(range(256)) * 64),
    "empty": lambda d: _write(os.path.join(d, "empty.csv"), b""),
    "header_only": lambda d: _write(os.path.join(d, "header.csv"), "id,status\n"),
    "directory": lambda d: (os.makedirs(os.path.join(d, "a_dir"), exist_ok=True), os.path.join(d, "a_dir"))[1],
    "nonexistent": lambda d: os.path.join(d, "no", "such", "file.csv"),
    "field_3mb": lambda d: _write(os.path.join(d, "big.csv"), "id,status\n1," + "x" * 3_000_000 + "\n"),
    "nul_bytes": lambda d: _write(os.path.join(d, "nul.csv"), b"id,status\n1,o\x00k\n"),
    "utf8_bom": lambda d: _write(os.path.join(d, "bom.csv"), b"\xef\xbb\xbfid,status\n1,ok\n"),
    "cr_only": lambda d: _write(os.path.join(d, "cr.csv"), b"id,status\r1,ok\r2,ok\r"),
    "mixed_eol": lambda d: _write(os.path.join(d, "mixed.csv"), b"id,status\r\n1,ok\n2,ok\r3,ok\r\n"),
    "non_utf8": lambda d: _write(os.path.join(d, "latin1.csv"), "id,status\n1,café\n".encode("latin-1")),
    "dangling_symlink": lambda d: _symlink(d, "dangling.csv", os.path.join(d, "gone.csv")),
    "symlink_loop": _loop,
    "unreadable": _unreadable,
    "spaces_unicode": lambda d: _write(os.path.join(d, "sp ace", "ünï cødé.csv"), "id,status\n1,ok\n"),
    "very_long_path": lambda d: os.path.join(d, *(["x" * 200] * 25), "f.csv"),
    "wrong_json_types": lambda d: _write(os.path.join(d, "types.json"),
                                         json.dumps({"log": [1, 2], "output": {"path": 5, "columns": "id"}})),
}

# Paths the invocations need besides the hostile one; built once per run.
def _fixtures(d):
    fx = {
        "ok_csv": _write(os.path.join(d, "fx", "ok.csv"), "id,status\n1,ok\n2,ok\n"),
        "doc": _write(os.path.join(d, "fx", "README.md"), "We have 2 tests and 2 rows.\n"),
        "log": _write(os.path.join(d, "fx", "log.txt"), "## [2026-10-24T10:00:00Z] Start\n\nUser Prompt:\nhi\n"),
        "usage": _write(os.path.join(d, "fx", "usage.jsonl"),
                        '{"provider":"a","model":"m","input_tokens":1,"output_tokens":2}\n'),
        "code": os.path.dirname(_write(os.path.join(d, "fx", "code", "a.py"), "LIMIT = 5\n")),
        "starter": os.path.dirname(_write(os.path.join(d, "fx", "starter", "AGENTS.md"), "You MUST write output.csv.\n")),
        "out_missing_dir": os.path.join(d, "fx", "nowhere", "deeper", "out.md"),
        "out_onto_dir": os.path.dirname(_write(os.path.join(d, "fx", "outdir", "keep.txt"), "x")),
        "out_onto_file": _write(os.path.join(d, "fx", "existing_file"), "x"),
        "tmp": os.path.join(d, "fx", "scratch"),
    }
    os.makedirs(fx["tmp"], exist_ok=True)
    return fx


S = lambda name: os.path.join(SCRIPTS, name)  # noqa: E731
T = lambda name: os.path.join(TOOLS, name)  # noqa: E731

# (script, argv template, documented exit codes). "{X}" is the hostile path; "{name}" is a fixture.
CASES = [
    (S("check_log.py"), ["{X}"], {0, 1, 2}),
    (S("check_log.py"), ["{log}", "--profile", "{X}"], {0, 1, 2}),
    (S("claim_audit.py"), ["{X}", "--repo", "{code}"], {0, 1, 2, 3}),
    (S("claim_audit.py"), ["{doc}", "--csv", "{X}"], {0, 1, 2, 3}),
    (S("claim_audit.py"), ["{doc}", "--constants", "{X}"], {0, 1, 2, 3}),
    (S("claim_audit.py"), ["{doc}", "--repo", "{X}"], {0, 1, 2, 3}),
    (S("contract_extract.py"), ["{X}"], {0, 2}),
    (S("contract_extract.py"), ["--diff", "{X}", "{starter}"], {0, 2}),
    (S("corpus_literals.py"), ["--data", "{X}", "--code", "{code}"], {0, 1, 2}),
    (S("corpus_literals.py"), ["--data", "{ok_csv}", "--code", "{X}"], {0, 1, 2}),
    (S("corpus_literals.py"), ["--data", "{ok_csv}", "--code", "{code}", "--spec", "{X}"], {0, 1, 2}),
    (S("corpus_literals.py"), ["--data", "{ok_csv}", "--code", "{code}", "--allowlist", "{X}"], {0, 1, 2}),
    (S("interview_drill.py"), ["{X}"], {0, 2}),
    (S("interview_drill.py"), ["{code}", "--constants", "{X}"], {0, 2}),
    (S("preflight.py"), ["{X}", "--columns", "id,status"], {0, 1, 2}),
    (S("preflight.py"), ["{ok_csv}", "--template", "{X}"], {0, 1, 2}),
    (S("preflight.py"), ["{ok_csv}", "--columns", "id,status", "--inputs", "{X}", "--id-col", "id"], {0, 1, 2}),
    (S("rerun_diff.py"), ["--id-col", "id", "{X}", "{ok_csv}"], {0, 1, 2}),
    (S("selfcheck.py"), ["{X}"], {0, 1, 2, 3, 4}),
    (S("usage_report.py"), ["{X}", "--price", "m=1:2", "--requests", "1"], {0, 2}),
    (T("footprint.py"), ["--skill-dir", "{X}"], {0, 1, 2}),
    (T("package_skill.py"), ["--skill-dir", "{X}", "--out", "{tmp}"], {0, 1, 2}),
    (T("validate_skill.py"), ["--skill-dir", "{X}", "--standalone"], {0, 1, 2}),
    (T("run_trigger_evals.py"), ["--offline", "--evals", "{X}"], {0, 1, 2}),
    (T("run_trigger_evals.py"), ["--offline", "--skill", "{X}"], {0, 1, 2}),
]

# Output-path cases: every --out (or --install) target that cannot be written as asked.
OUT_TARGETS = ("out_missing_dir", "out_onto_dir")
OUT_CASES = [
    (S("contract_extract.py"), ["{starter}", "--out", "{O}"], {0, 2}),
    (S("interview_drill.py"), ["{code}", "--out", "{O}"], {0, 2}),
    (S("usage_report.py"), ["{usage}", "--price", "m=1:2", "--requests", "1", "--out", "{O}"], {0, 2}),
    (T("package_skill.py"), ["--out", "{out_onto_file}"], {0, 2}),
    (T("package_skill.py"), ["--out", "{tmp}", "--install", "{out_onto_file}"], {0, 2}),
]

# Configs with wrong JSON types, for the scripts that read JSON.
BAD_CONFIGS = [
    {"claims": {"docs": "README.md"}},
    {"output": {"path": ["a"], "columns": ["id"]}},
    {"corpus_literals": {"data": ["a.csv"], "code": ["c"], "min_length": "six"}},
    {"output": {"path": "o.csv", "columns": ["id"], "enums": {"status": "ok"}}},
    {"log": None},
    [],
    "text",
]


def _run(argv):
    try:
        proc = subprocess.run([sys.executable, "-W", "error"] + argv, capture_output=True, text=True,
                              errors="replace", timeout=60, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    return proc.returncode, proc.stdout + proc.stderr


def _fill(template, values):
    return [a.format(**values) for a in template]


class CliMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp(prefix="cli_matrix_")
        cls.fx = _fixtures(cls.d)
        cls.inputs = {}
        for name, build in INPUTS.items():
            sub = os.path.join(cls.d, "in_" + name)
            os.makedirs(sub)
            cls.inputs[name] = build(sub)

    @classmethod
    def tearDownClass(cls):
        for dirpath, dirnames, _ in os.walk(cls.d):
            for p in [dirpath] + [os.path.join(dirpath, n) for n in dirnames]:
                if not os.path.islink(p):
                    os.chmod(p, 0o755)
        unreadable = cls.inputs.get("unreadable")
        if unreadable:
            os.chmod(unreadable, 0o644)
        shutil.rmtree(cls.d, ignore_errors=True)

    def check_all(self, jobs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda j: (j, _run(j[1])), jobs))
        for (label, argv, codes), (rc, out) in results:
            with self.subTest(case=label):
                self.assertNotIn("Traceback", out, f"{label}\n{out[-1500:]}")
                self.assertIn(rc, codes, f"{label}: exit {rc}, documented {sorted(codes)}\n{out[-800:]}")

    def test_every_cli_on_every_hostile_input(self):
        jobs = []
        for name, path in self.inputs.items():
            if path is None:
                continue
            values = dict(self.fx, X=path)
            for script, template, codes in CASES:
                jobs.append((f"{os.path.basename(script)} {' '.join(template)} [{name}]",
                             [script] + _fill(template, values), codes))
        self.assertGreater(len(jobs), 300)
        self.check_all(jobs)

    def test_unwritable_output_paths(self):
        jobs = []
        for target in OUT_TARGETS:
            values = dict(self.fx, O=self.fx[target])
            for script, template, codes in OUT_CASES:
                jobs.append((f"{os.path.basename(script)} {' '.join(template)} [{target}]",
                             [script] + _fill(template, values), codes))
        self.check_all(jobs)

    def test_configs_with_wrong_json_types(self):
        jobs = []
        for i, cfg in enumerate(BAD_CONFIGS):
            p = _write(os.path.join(self.d, "cfg", f"bad{i}.json"), json.dumps(cfg))
            jobs.append((f"selfcheck bad{i}", [S("selfcheck.py"), p], {4}))
            jobs.append((f"check_log --profile bad{i}", [S("check_log.py"), self.fx["log"], "--profile", p], {2}))
            jobs.append((f"run_trigger_evals --evals bad{i}", [T("run_trigger_evals.py"), "--offline", "--evals", p], {2}))
        self.check_all(jobs)


if __name__ == "__main__":
    unittest.main()
