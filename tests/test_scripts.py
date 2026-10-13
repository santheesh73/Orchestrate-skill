"""Smoke tests for the bundled scripts against small fixtures. Run: python -m unittest discover tests"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(HERE, "..", "hackerrank-orchestrate", "scripts"))

sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import check_log  # noqa: E402
import run_trigger_evals  # noqa: E402
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


class CheckLogProfiles(unittest.TestCase):
    """The profile path must reproduce v2.0.0 output exactly on the shipped fixtures."""

    def golden(self, name):
        with open(f(os.path.join("golden", name)), encoding="utf-8") as fh:
            return fh.read()

    def assert_same(self, args, golden_name):
        rc, out = run(check_log, args)
        self.assertEqual(out + f"rc={rc}\n", self.golden(golden_name))

    def test_default_and_profile_match_v200(self):
        regex = check_log.DEFAULT_ENTRY_REGEX
        for log in ("log_good", "log_bad"):
            g = f"check_log_v2.0.0_{log}.out"
            self.assert_same([f(log + ".txt")], g)
            self.assert_same([f(log + ".txt"), "--profile", "sept-2026"], g)
            self.assert_same([f(log + ".txt"), "--entry-regex", regex, "--prompt-header", "User Prompt"], g)
        self.assert_same([f("log_good.txt"), "--expect-tool", "Claude Code", "--profile", "sept-2026"],
                         "check_log_v2.0.0_log_good_expect.out")

    def test_list_profiles(self):
        rc, out = run(check_log, ["--list-profiles"])
        self.assertEqual(rc, 0)
        self.assertIn("sept-2026 (default)", out)
        self.assertIn("june-2026", out)
        self.assertNotIn("template", out)

    def test_june_profile_accepts_agent_line_in_session_start(self):
        self.assertEqual(run(check_log, [f("log_june.txt")])[0], 1)  # sept rules: session start lacks tool=
        rc, out = run(check_log, [f("log_june.txt"), "--profile", "june-2026"])
        self.assertEqual(rc, 0, out)

    def test_profile_by_path_and_unknown_profile(self):
        path = os.path.join(HERE, "..", "hackerrank-orchestrate", "assets", "editions", "template.json")
        self.assertEqual(run(check_log, [f("log_good.txt"), "--profile", path])[0], 0)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(run(check_log, [f("log_good.txt"), "--profile", "nope"])[0], 2)
        self.assertIn("unknown profile", err.getvalue())

    def test_unmatched_format_warns_instead_of_silent(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "log.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("=== 2026-10-24 SESSION ===\ntool=Claude Code\n")
            rc, out = run(check_log, [p])
        self.assertEqual(rc, 1)
        self.assertIn("matches no shipped profile", out)


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
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
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


class TriggerEvals(unittest.TestCase):
    def test_offline_is_deterministic_and_labelled_proxy(self):
        rc1, out1 = run(run_trigger_evals, ["--offline"])
        rc2, out2 = run(run_trigger_evals, ["--offline"])
        self.assertEqual((rc1, out1), (rc2, out2))
        self.assertIn("not model behavior", out1)
        self.assertRegex(out1, r"precision=\d\.\d\d recall=\d\.\d\d")

    def test_offline_floor_fails_when_unmet(self):
        rc, _ = run(run_trigger_evals, ["--offline", "--min-recall", "1.01"])
        self.assertEqual(rc, 1)

    def test_live_without_key_is_unknown_and_makes_no_request(self):
        calls = []
        orig, old_key = run_trigger_evals.ask, os.environ.pop("ANTHROPIC_API_KEY", None)
        run_trigger_evals.ask = lambda *a, **k: calls.append(a)
        try:
            rc, out = run(run_trigger_evals, ["--live", "--model", "any"])
        finally:
            run_trigger_evals.ask = orig
            if old_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_key
        self.assertEqual(rc, 0)
        self.assertIn("UNKNOWN", out)
        self.assertEqual(calls, [])

    def test_live_requires_model(self):
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-not-a-key"
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                rc, _ = run(run_trigger_evals, ["--live"])
        finally:
            if old_key is None:
                del os.environ["ANTHROPIC_API_KEY"]
            else:
                os.environ["ANTHROPIC_API_KEY"] = old_key
        self.assertEqual(rc, 2)
        self.assertNotIn("test-not-a-key", err.getvalue())

    def test_splits_are_stable_and_both_present(self):
        with open(run_trigger_evals.DEFAULT_EVALS, encoding="utf-8") as fh:
            evals = json.load(fh)
        splits = {run_trigger_evals.split_of(e["query"]) for e in evals}
        self.assertEqual(splits, {"train", "test"})


if __name__ == "__main__":
    unittest.main()
