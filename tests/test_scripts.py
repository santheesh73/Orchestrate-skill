"""Smoke tests for the bundled scripts against small fixtures. Run: python -m unittest discover tests"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(HERE, "..", "hackerrank-orchestrate", "scripts"))

import check_log  # noqa: E402
import interview_drill  # noqa: E402
import preflight  # noqa: E402
import rerun_diff  # noqa: E402
import usage_report  # noqa: E402


def f(name):
    return os.path.join(FIX, name)


def run(mod, args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = mod.main(args)
    return rc, out.getvalue()


class CheckLog(unittest.TestCase):
    def test_good_log_passes(self):
        rc, out = run(check_log, [f("log_good.txt"), "--expect-tool", "Claude Code"])
        self.assertEqual(rc, 0, out)

    def test_bad_log_flags_every_problem(self):
        rc, out = run(check_log, [f("log_bad.txt")])
        self.assertEqual(rc, 1)
        for needle in ("placeholder", "model name", "generic label", "block is empty",
                       "goes backwards", "exactly one", "no 'User Prompt' block", "possible secret"):
            self.assertIn(needle, out)

    def test_expect_tool_mismatch(self):
        rc, out = run(check_log, [f("log_good.txt"), "--expect-tool", "Codex CLI"])
        self.assertEqual(rc, 1)
        self.assertIn("expected 'Codex CLI'", out)

    def test_harness_names_are_not_model_names(self):
        for ok in ("Claude Code", "Codex CLI", "Gemini CLI", "Cursor"):
            self.assertIsNone(check_log.tool_problem(ok, None), ok)
        for bad in ("claude-sonnet-4-5", "gpt-4o", "Opus 4.1", "gemini 2.5 pro"):
            self.assertIsNotNone(check_log.tool_problem(bad, None), bad)


class Preflight(unittest.TestCase):
    ARGS = ["--template", f("template.csv"), "--inputs", f("inputs.csv"), "--id-col", "request_id",
            "--enum", "status=approved|wait|declined", "--nonempty", "explanation"]

    def test_good_output_passes(self):
        rc, out = run(preflight, [f("output_good.csv")] + self.ARGS)
        self.assertEqual(rc, 0, out)

    def test_bad_output_flags_every_problem(self):
        rc, out = run(preflight, [f("output_bad.csv")] + self.ARGS)
        self.assertEqual(rc, 1)
        for needle in ("wrong order", "duplicate ids", "no output row", "not in the inputs",
                       "off-enum", "blank explanation"):
            self.assertIn(needle, out)


class RerunDiff(unittest.TestCase):
    def test_identical(self):
        rc, out = run(rerun_diff, [f("output_good.csv"), f("output_good.csv"), "--id-col", "request_id"])
        self.assertEqual(rc, 0)
        self.assertIn("0 rows changed", out)

    def test_changed_rows_counted(self):
        rc, out = run(rerun_diff, [f("output_good.csv"), f("run_b.csv"), "--id-col", "request_id",
                                   "--ignore", "explanation"])
        self.assertEqual(rc, 1)
        self.assertIn("1 of 3", out)


class UsageReport(unittest.TestCase):
    def test_report_filters_run_and_totals(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "usage_report.md")
            rc, _ = run(usage_report, [f("usage.jsonl"), "--run-id", "final",
                                       "--price", "model-a=3:15:0.3:3.75", "--price", "model-b=1:5",
                                       "--out", path])
            self.assertEqual(rc, 0)
            text = open(path, encoding="utf-8").read()
        self.assertIn("| Model calls | 3 |", text)
        self.assertIn("| Input tokens | 4,100 |", text)
        self.assertIn("| Requests processed | 2 |", text)
        # (4000*3 + 600*15 + 500*0.3)/1e6 + (100*1 + 10*5)/1e6
        self.assertIn("$0.0213", text)

    def test_missing_price_is_not_estimated(self):
        rc, out = run(usage_report, [f("usage.jsonl"), "--run-id", "final"])
        self.assertEqual(rc, 0)
        self.assertIn("not estimated", out)


class InterviewDrill(unittest.TestCase):
    def test_finds_decisions_and_missing_constants(self):
        rc, out = run(interview_drill, [f("code"), "--constants", f("CONSTANTS.md")])
        self.assertEqual(rc, 0)
        self.assertIn("`MAX_STEPS`", out.split("## Named constants")[0])  # listed as missing
        self.assertIn("decide.py:10", out)  # threshold with a named constant
        self.assertIn("0.35", out)          # literal threshold
        self.assertIn("breaks ties", out)   # sorted(key=...)
        self.assertIn("`median`", out)
        self.assertIn("temperature", out)


if __name__ == "__main__":
    unittest.main()
