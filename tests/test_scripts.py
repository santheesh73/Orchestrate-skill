"""Smoke tests for the bundled scripts against small fixtures. Run: python -m unittest discover tests"""

import contextlib
import io
import shutil
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
import claim_audit  # noqa: E402
import contract_extract  # noqa: E402
import corpus_literals  # noqa: E402
import selfcheck  # noqa: E402
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


PROJECT = f("project")


def copy_project(d):
    dest = os.path.join(d, "project")
    shutil.copytree(PROJECT, dest)
    return dest


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class SelfCheck(unittest.TestCase):
    def test_clean_project_passes_every_check(self):
        rc, out = run(selfcheck, [os.path.join(PROJECT, "selfcheck.json")])
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count("PASS"), 7)  # six rows plus the summary line

    def test_unconfigured_section_is_unknown_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            proj = copy_project(d)
            cfg_path = os.path.join(proj, "selfcheck.json")
            with open(cfg_path, encoding="utf-8") as fh:
                cfg = json.load(fh)
            del cfg["claims"]
            write(cfg_path, json.dumps(cfg))
            rc, out = run(selfcheck, [cfg_path])
        self.assertEqual(rc, 2)
        self.assertRegex(out, r"claims\s+UNKNOWN")

    def test_worst_result_wins_and_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            proj = copy_project(d)
            os.remove(os.path.join(proj, "code", "evaluation", "usage_report.md"))
            write(os.path.join(proj, "README.md"), "The suite has 9 tests.\n")
            rc, out = run(selfcheck, [os.path.join(proj, "selfcheck.json")])
        self.assertEqual(rc, 3)
        self.assertRegex(out, r"usage_report\s+FAIL")
        self.assertRegex(out, r"claims\s+WARN")

    def test_bad_config(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            write(p, json.dumps({"logs": {}}))
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc, _ = run(selfcheck, [p])
        self.assertEqual(rc, 4)
        self.assertIn("unknown config sections", err.getvalue())


class CorpusLiterals(unittest.TestCase):
    DATA = [os.path.join(PROJECT, "dataset", "requests.csv")]

    def test_flags_ids_strings_and_number_tuples(self):
        found = corpus_literals.scan(self.DATA, [f("coupled")], [os.path.join(PROJECT, "problem_statement.md")])
        text = "\n".join(m for _, _, m in found)
        self.assertIn("'u_7Q2'", text)
        self.assertIn("'buy laptop'", text)
        self.assertIn("(1200.5,90)", text)
        self.assertNotIn("'approved'", text)  # not in the dataset inputs
        self.assertNotIn("'rent'", text)      # below the length floor and not id-like

    def test_spec_and_allowlist_suppress(self):
        with tempfile.TemporaryDirectory() as d:
            allow = os.path.join(d, "allow.txt")
            write(allow, "# justified\nu_7Q2\nbuy laptop  # domain term\n1200.5,90\n")
            found = corpus_literals.scan(self.DATA, [f("coupled")], [], allow)
        self.assertEqual(found, [])

    def test_clean_code_exit_zero_and_coupled_exit_one(self):
        base = ["--data", self.DATA[0], "--spec", os.path.join(PROJECT, "problem_statement.md")]
        self.assertEqual(run(corpus_literals, base + ["--code", os.path.join(PROJECT, "code")])[0], 0)
        self.assertEqual(run(corpus_literals, base + ["--code", f("coupled")])[0], 1)

    def test_quoted_commas_bom_and_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            data = os.path.join(d, "data.csv")
            with open(data, "w", encoding="utf-8-sig", newline="") as fh:
                fh.write('id,name\nüser_01,"Café, Zürich branch"\n')
            code = os.path.join(d, "x.py")
            write(code, 'A = "Café, Zürich branch"\nB = "üser_01"\n')
            found = corpus_literals.scan([data], [code])
        self.assertEqual(len(found), 2)

    def test_docstrings_and_headers_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            data = os.path.join(d, "data.csv")
            write(data, "request_identifier,text\nreq_0001,hello world again\n")
            code = os.path.join(d, "x.py")
            write(code, '"""hello world again"""\nCOL = "request_identifier"\n')
            self.assertEqual(corpus_literals.scan([data], [code]), [])


class ClaimAudit(unittest.TestCase):
    def test_matching_claims_ok(self):
        results, live = claim_audit.audit([os.path.join(PROJECT, "README.md")], PROJECT,
                                          [os.path.join(PROJECT, "output.csv")], os.path.join(PROJECT, "CONSTANTS.md"))
        self.assertEqual(live["test"], [2])
        self.assertEqual(live["constant"], [2])
        self.assertTrue(all(r[0] == "OK" for r in results), results)

    def test_mismatch_is_a_hint_unless_strict(self):
        with tempfile.TemporaryDirectory() as d:
            doc = os.path.join(d, "README.md")
            write(doc, "We ship 1,234 tests and 7 rows. Also 5 requests.\n")
            args = [doc, "--repo", PROJECT, "--csv", os.path.join(PROJECT, "output.csv")]
            rc, out = run(claim_audit, args)
            self.assertEqual(rc, 0)
            self.assertIn("'1,234 tests' (live: 2)", out)
            self.assertIn("hints, not proof", out)
            self.assertEqual(run(claim_audit, args + ["--strict"])[0], 1)

    def test_unchecked_kind_without_source(self):
        results, _ = claim_audit.audit([os.path.join(PROJECT, "README.md")])
        self.assertTrue(all(r[0] == "UNCHECKED" for r in results))

    def test_csv_with_quoted_newlines_counts_rows(self):
        self.assertEqual(claim_audit.count_csv_rows(f("output_good.csv")), 3)

    def test_fixture_tests_excluded_by_default(self):
        # Regression: v2.1.0 counted the fixture project's tests and reported 71 for a 69-test suite.
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "tests", "test_a.py"), "def test_one():\n    pass\ndef test_two():\n    pass\n")
            write(os.path.join(d, "tests", "fixtures", "proj", "tests", "test_b.py"),
                  "def test_x():\n    pass\ndef test_y():\n    pass\ndef test_z():\n    pass\n")
            write(os.path.join(d, "vendor", "test_c.py"), "def test_v():\n    pass\n")
            self.assertEqual(claim_audit.count_tests(d), 3)
            self.assertEqual(claim_audit.count_tests(d, ()), 6)
            self.assertEqual(claim_audit.count_tests(d, ("tests/fixtures", "vendor")), 2)
            self.assertEqual(claim_audit.count_tests(d, ("ven*",)), 5)
            doc = os.path.join(d, "README.md")
            write(doc, "2 tests\n")
            self.assertIn("0 mismatches", run(claim_audit, [doc, "--repo", d, "--exclude", "vendor"])[1])
            self.assertIn("(live: 6)", run(claim_audit, [doc, "--repo", d, "--no-default-exclude"])[1])

    def test_repo_count_equals_real_suite(self):
        suite = unittest.defaultTestLoader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
        self.assertEqual(claim_audit.count_tests(os.path.join(HERE, "..")), suite.countTestCases())

    def test_selfcheck_on_this_repo_reports_the_suite_count(self):
        suite = unittest.defaultTestLoader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
        rc, out = run(selfcheck, [os.path.join(HERE, "..", "selfcheck.json")])
        self.assertRegex(out, r"claims\s+PASS")
        self.assertIn(f"tests={suite.countTestCases()}", out)


class ContractExtract(unittest.TestCase):
    def test_checklist_categories_with_source_lines(self):
        items = contract_extract.extract_dir(f(os.path.join("starters", "new")))
        cats = {c for c, _, _ in items}
        self.assertTrue({"must", "must_not", "required_file", "columns", "allowed", "order"} <= cats, cats)
        self.assertIn(("required_file", "evaluation/usage_report.md", "AGENTS.md:5"), items)

    def test_diff_reports_added_and_changed(self):
        rc, out = run(contract_extract, ["--diff", f(os.path.join("starters", "old")), f(os.path.join("starters", "new"))])
        self.assertEqual(rc, 0)
        self.assertIn("ADDED", out)
        self.assertIn("usage_report.md", out)
        self.assertIn("CHANGED", out)
        self.assertIn("request_id,status,amount,explanation", out)
        self.assertIn("heuristic", out)

    def test_identical_editions(self):
        d = f(os.path.join("starters", "old"))
        rc, out = run(contract_extract, ["--diff", d, d])
        self.assertIn("No requirement lines differ.", out)

    def test_missing_files_is_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(run(contract_extract, [d])[0], 2)


if __name__ == "__main__":
    unittest.main()
