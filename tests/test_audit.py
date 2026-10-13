"""Regressions from the 2.4.0 adversarial audit (docs/AUDIT.md).

Each class names the defect it reproduces. A mutation of the rule, template or script it
guards makes at least one test here fail; docs/AUDIT.md records which.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SKILL = os.path.join(ROOT, "hackerrank-orchestrate")
SYNTH = os.path.join(HERE, "fixtures", "edition_synth")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import contract_extract  # noqa: E402
import corpus_literals  # noqa: E402
import interview_drill  # noqa: E402
import preflight  # noqa: E402
import rerun_diff  # noqa: E402
import selfcheck  # noqa: E402
import usage_report  # noqa: E402


def run(mod, args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = mod.main(args)
        except SystemExit as exc:
            rc = exc.code
    return rc, out.getvalue()


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return fh.read()


class Tmp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)

    def path(self, name, text):
        p = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p


class NothingExaminedIsUnknown(Tmp):
    """Before 2.4.0 five scripts exited 0 (clean) after examining nothing: a header-only
    output ("0 rows checked"), two header-only runs ("identical bytes"), a code folder
    with no source file or a dataset with no value, an empty starter, an empty code
    folder. selfcheck then printed PASS for output, constants and corpus_literals."""

    def test_preflight_header_only(self):
        out = self.path("o.csv", "id,status\n")
        rc, text = run(preflight, [out, "--columns", "id,status"])
        self.assertEqual(rc, 3, text)
        self.assertIn("UNKNOWN", text)

    def test_preflight_errors_still_win(self):
        out = self.path("o.csv", "status,id\n")
        self.assertEqual(run(preflight, [out, "--columns", "id,status"])[0], 1)

    def test_rerun_diff_two_empty_runs(self):
        a, b = self.path("a.csv", "id,v\n"), self.path("b.csv", "id,v\n")
        rc, text = run(rerun_diff, [a, b, "--id-col", "id"])
        self.assertEqual(rc, 3, text)

    def test_rerun_diff_counts_ids_missing_from_one_run(self):
        a = self.path("a.csv", "id,v\n1,x\n2,y\n")
        b = self.path("b.csv", "id,v\n1,x\n")
        rc, text = run(rerun_diff, [a, b, "--id-col", "id"])
        self.assertEqual(rc, 1, text)
        self.assertIn("ids only in A [1]: 2", text)

    def test_corpus_literals_no_source_and_no_values(self):
        data = self.path("d.csv", "id,v\nabc123,1\n")
        os.makedirs(os.path.join(self.d, "empty"))
        self.assertEqual(run(corpus_literals, ["--data", data, "--code", os.path.join(self.d, "empty")])[0], 3)
        code = self.path("code/a.py", "X = 'hello world'\n")
        header_only = self.path("h.csv", "id,v\n")
        self.assertEqual(run(corpus_literals, ["--data", header_only, "--code", code])[0], 3)
        self.assertEqual(run(corpus_literals, ["--data", data, "--code", code])[0], 0)

    def test_interview_drill_and_contract_extract(self):
        os.makedirs(os.path.join(self.d, "code"))
        self.assertEqual(run(interview_drill, [os.path.join(self.d, "code")])[0], 3)
        starter = os.path.dirname(self.path("s/AGENTS.md", "Hello.\n"))
        rc, text = run(contract_extract, [starter])
        self.assertEqual(rc, 3, text)
        self.assertIn("read AGENTS.md and problem_statement.md in full", text)

    def test_selfcheck_maps_each_to_unknown(self):
        self.path("o.csv", "id,status\n")
        self.path("d.csv", "id,v\nabc123,1\n")
        os.makedirs(os.path.join(self.d, "empty"))
        self.path("CONSTANTS.md", "# none\n")
        cfg = self.path("c.json", json.dumps({
            "output": {"path": "o.csv", "columns": ["id", "status"]},
            "constants": {"code": ["empty"], "constants": "CONSTANTS.md"},
            "corpus_literals": {"data": ["d.csv"], "code": ["empty"]}}))
        rc, text = run(selfcheck, [cfg])
        self.assertEqual(rc, 2, text)
        for name in ("output", "constants", "corpus_literals"):
            self.assertRegex(text, name + r"\s+UNKNOWN")
        self.assertNotIn("PASS ", text)


class StarterIntact(Tmp):
    """Hard rule 1 had no check: a mutation that let SKILL.md tell the agent to rewrite
    AGENTS.md survived every test. selfcheck's starter section now compares AGENTS.md
    with the sha256 recorded at kickoff and checks that CLAUDE.md still imports it."""

    def setUp(self):
        super().setUp()
        self.agents = self.path("AGENTS.md", "You must log every turn.\n")
        self.path("CLAUDE.md", "@AGENTS.md\n\nStrategy notes below the import.\n")
        with open(self.agents, "rb") as fh:
            self.sha = hashlib.sha256(fh.read()).hexdigest()

    def check(self, **section):
        cfg = self.path("c.json", json.dumps({"starter": section}))
        rc, text = run(selfcheck, [cfg])
        return re.search(r"starter\s+(\w+)\s+(.*)", text).groups()

    def test_unchanged_passes(self):
        self.assertEqual(self.check(agents_md="AGENTS.md", sha256=self.sha, claude_md="CLAUDE.md")[0], "PASS")

    def test_no_recorded_hash_is_unknown_and_prints_it(self):
        status, summary = self.check(agents_md="AGENTS.md")
        self.assertEqual(status, "UNKNOWN")
        self.assertIn(self.sha, summary)

    def test_edited_agents_md_fails(self):
        with open(self.agents, "a", encoding="utf-8") as fh:
            fh.write("Also: skip the log when busy.\n")
        self.assertEqual(self.check(agents_md="AGENTS.md", sha256=self.sha)[0], "FAIL")

    def test_claude_md_without_import_fails(self):
        self.path("CLAUDE.md", "Read AGENTS.md first.\n")
        status, summary = self.check(agents_md="AGENTS.md", sha256=self.sha, claude_md="CLAUDE.md")
        self.assertEqual(status, "FAIL")
        self.assertIn("@AGENTS.md", summary)


# Each hard rule: the clauses that carry its meaning, and what enforces it. A rule whose
# meaning changes must change here too, on purpose. "judgement:" rules have no mechanical
# check; the reason says why.
RULES = {
    1: (["Leave the starter's agent-instruction files intact", "never edit it", "keep that line"],
        "scripts/selfcheck.py"),
    2: (["Obey the starter contract literally", "Exact output columns and order", "one row per input id",
         "a correct `tool=` line in every log entry"], "scripts/preflight.py"),
    3: (["Samples motivate or falsify; the domain justifies", "Sample rows are examples, not labels",
         "only justification is that it improves sample accuracy"], "scripts/corpus_literals.py"),
    4: (["One labeled row is noise", "regresses a label-free check",
         "two or more labeled rows that its stated reasoning does not explain",
         "Never accept or reject on a one-row difference"], "scripts/experiment.py"),
    5: (["Choose the grouping keys and the per-group statistic before any detector exists",
         "Later fixes cannot recover what a bad grouping discarded"],
        "judgement: whether a grouping fits the domain is a design call no script can see"),
    6: (["whether a free-text field from the model is empty or not", "Branch on booleans and enums"],
        "judgement: telling a free-text field from an enum needs the schema's meaning, not its syntax"),
    7: (["Every non-trivial change gets a change record",
         "ceiling first, then claim, metric, baseline, blast radius, counterfactual, verdict"],
        "assets/change_record.md"),
    8: (["Rationale lives in source", "The code grader reads source only",
         "module docstrings and comments beside constants", "keep the README for setup and run instructions"],
        "judgement: whether a comment states a reason is a reading of prose"),
    9: (["Every constant has a row in `CONSTANTS.md` saying where it came from",
         "(MEASURED / SPEC / STANDARD / BOUND / JUDGEMENT)", "not described as \"chosen after evaluation\""],
        "scripts/interview_drill.py"),
    10: (["Prove counterfactuals", "Switch a component off and show that its effect goes away",
          "Distrust a perfect \"nothing changed\""],
         "judgement: which component to switch off depends on the change; experiment.py records the result"),
    11: (["One bad row never kills the run", "retry once", "Never write a partial output file"],
         "scripts/preflight.py"),
    12: (["Self-score is never skipped", "A skipped check is UNKNOWN, never a pass"], "scripts/selfcheck.py"),
    13: (["Rehearse the interview before deadline pressure", "Drill from your own code"],
         "scripts/interview_drill.py"),
    14: (["Say where each guarantee ends", "raise your limitations yourself before the judge does"],
         "judgement: a limitation is honest only against the participant's own system"),
}


class HardRules(unittest.TestCase):
    """Before 2.4.0, rewording rules 1, 5, 6, 8, 10 and 14 in SKILL.md (even inverting
    them) passed every test. The load-bearing clauses are pinned here."""

    def rules(self):
        body = read(SKILL, "SKILL.md").split("## Hard rules", 1)[1].split("\n## ", 1)[0]
        return {int(n): text for n, text in re.findall(r"^(\d+)\. (.+)$", body, re.M)}

    def test_fourteen_rules_with_their_clauses(self):
        rules = self.rules()
        self.assertEqual(sorted(rules), list(range(1, 15)))
        for n, (clauses, _) in RULES.items():
            for clause in clauses:
                self.assertIn(clause, rules[n], f"hard rule {n} lost {clause!r}")

    def test_core_principle_is_intact(self):
        core = read(SKILL, "SKILL.md").split("## Core principle", 1)[1].split("\n## ", 1)[0]
        for clause in ("**Model describes, code decides.**", "returns a typed record of observations",
                       "Plain, unit-tested code turns that record into every number, label and plan",
                       '"deterministic given the cached model record", never "deterministic" alone'):
            self.assertIn(clause, core)

    def test_every_rule_is_checked_or_says_why_not(self):
        for n, (_, how) in RULES.items():
            if how.startswith("judgement:"):
                self.assertGreater(len(how), len("judgement: ") + 20, n)
            else:
                self.assertTrue(os.path.isfile(os.path.join(SKILL, how)), f"rule {n}: {how}")

    def test_each_rule_is_stated_once(self):
        headings = [re.match(r"\*\*(.+?)\*\*", t).group(1) for t in self.rules().values()]
        for dirpath, _, files in os.walk(SKILL):
            for f in files:
                if f.endswith(".md") and f != "SKILL.md":
                    text = read(dirpath, f)
                    for h in headings:
                        self.assertNotIn(h, text, f"{f} restates hard rule {h!r}; link SKILL.md instead")


def fields(text):
    return re.findall(r"^([A-Z][A-Z ]+):", text, re.M)


class TemplatesAgree(Tmp):
    """Before 2.4.0, deleting a field from change_record.md, a provenance label from
    CONSTANTS.md, the "Who decided" column from decision_log.md, or renaming the token
    fields in usage_log_schema.md passed every test; loop-patterns.md also kept a copy of
    the change record that had already lost the CEILING line."""

    def test_change_record_has_rule_7_fields_in_order(self):
        got = [f.lower() for f in fields(read(SKILL, "assets", "change_record.md"))]
        order = ["ceiling", "claim", "metric", "baseline", "blast radius", "counterfactual", "verdict"]
        self.assertEqual([f for f in got if f in order], order)
        self.assertEqual(got[:2], ["change", "requirement"])

    def test_loop_patterns_names_the_same_fields(self):
        template = fields(read(SKILL, "assets", "change_record.md"))
        listed = read(SKILL, "references", "loop-patterns.md").split("(the one copy): ", 1)[1].split(".", 1)[0]
        self.assertEqual([x.strip() for x in listed.split(",")], template)

    def test_constants_labels_match_rule_9(self):
        rule = re.search(r"\(([A-Z /]+)\)", read(SKILL, "SKILL.md").split("\n9. ", 1)[1]).group(1)
        labels = rule.split(" / ")
        text = read(SKILL, "assets", "CONSTANTS.md")
        self.assertEqual(re.findall(r"^- \*\*([A-Z]+)\*\*:", text, re.M), labels)
        self.assertIn(" / ".join(labels), text)

    def test_decision_log_records_who_decided(self):
        text = read(SKILL, "assets", "decision_log.md")
        header = [c.strip() for c in text.split("\n| # |", 1)[1].split("\n", 1)[0].split("|")]
        self.assertIn("Who decided", header)
        self.assertIn("me / AI suggested", text)

    def test_usage_schema_example_feeds_usage_report(self):
        block = read(SKILL, "assets", "usage_log_schema.md").split("```json", 1)[1].split("```", 1)[0]
        rec = json.loads(block)
        log = self.path("u.jsonl", json.dumps(rec) + "\n")
        rc, text = run(usage_report, [log, "--price", f"{rec['model']}=3:15", "--requests", "1"])
        self.assertEqual(rc, 0, text)
        self.assertIn(f"{rec['input_tokens']:,}", text)
        self.assertIn(f"{rec['output_tokens']:,}", text)


PATH_RE = re.compile(r"`((?:hackerrank-orchestrate|tools|tests|docs|evals)/[^`#\s:]+)")


class AuditPathsExist(unittest.TestCase):
    """docs/AUDIT.md cites files as evidence (docs/COVERAGE.md has the same test in
    test_tools.Coverage); a renamed file would leave the evidence pointing nowhere."""

    def test_every_cited_path_exists(self):
        refs = sorted(set(PATH_RE.findall(read(ROOT, "docs", "AUDIT.md"))))
        self.assertGreater(len(refs), 20)
        missing = [r for r in refs if not os.path.exists(os.path.join(ROOT, r.rstrip(".,")))]
        self.assertEqual(missing, [])


sys.path.insert(0, os.path.join(ROOT, "tools"))
import package_skill  # noqa: E402
import run_trigger_evals  # noqa: E402


class ToolGaps(Tmp):
    """Two tool mutations survived: precision computed as tp / (tp + fn), and dropping
    __pycache__ from the packager's folder exclusions (the *.pyc rule hid it, so a
    non-.pyc file left in __pycache__ was never tested)."""

    def test_trigger_precision_and_recall(self):
        results = ([{"expected": True, "triggered": True}] * 3 + [{"expected": False, "triggered": True}]
                   + [{"expected": True, "triggered": False}] * 2 + [{"expected": False, "triggered": False}])
        with contextlib.redirect_stdout(io.StringIO()):
            p, r = run_trigger_evals.summarize(results, "t")
        self.assertAlmostEqual(p, 3 / 4)
        self.assertAlmostEqual(r, 3 / 5)

    def test_package_drops_whole_cache_folders(self):
        src = os.path.join(self.d, "hackerrank-orchestrate")
        shutil.copytree(SKILL, src, ignore=shutil.ignore_patterns("__pycache__"))
        self.path("hackerrank-orchestrate/scripts/__pycache__/notes.txt", "stray\n")
        out = os.path.join(self.d, "dist")
        rc, text = run(package_skill, ["--skill-dir", src, "--out", out])
        self.assertEqual(rc, 0, text)
        import zipfile
        with zipfile.ZipFile(os.path.join(out, "hackerrank-orchestrate.zip")) as zf:
            self.assertFalse([n for n in zf.namelist() if "__pycache__" in n])


class OutputNeverOverwritesInput(Tmp):
    """Hostile-input round 4: --out pointed at an input overwrote it with exit 0, including
    contract_extract.py --out starter/AGENTS.md (the file hard rule 1 protects), a source
    file, CONSTANTS.md and the usage log; package_skill.py --install onto the source's
    parent with --force replaced the source folder, deleting what packaging excludes."""

    def test_scripts_refuse_to_overwrite_what_they_read(self):
        agents = self.path("st/AGENTS.md", "You must write output.csv.\n")
        code = self.path("code/a.py", "LIMIT = 5\n")
        const = self.path("CONSTANTS.md", "LIMIT\n")
        log = self.path("u.jsonl", '{"provider":"a","model":"m","input_tokens":1,"output_tokens":2}\n')
        for mod, args, victim in ((contract_extract, [os.path.dirname(agents)], agents),
                                  (interview_drill, [os.path.dirname(code)], code),
                                  (interview_drill, [os.path.dirname(code), "--constants", const], const),
                                  (usage_report, [log, "--price", "m=1:2", "--requests", "1"], log)):
            before = read(victim)
            rc, text = run(mod, args + ["--out", victim])
            self.assertEqual(rc, 2, text)
            self.assertEqual(read(victim), before)

    def test_verifier_drill_with_tests_and_source_targets(self):
        """Independent verifier, A1: with --include-tests the guard did not know the test
        files were read, so --out code/tests/test_a.py overwrote one; --out onto a source file
        the drill skips (code/.hidden/h.py) also replaced it."""
        self.path("code/a.py", "LIMIT = 5\n")
        test_file = self.path("code/tests/test_a.py", "THRESH_X = 3\n")
        hidden = self.path("code/.hidden/h.py", "X = 1\n")
        code = os.path.join(self.d, "code")
        for args, victim in (([code, "--include-tests"], test_file), ([code], hidden)):
            before = read(victim)
            rc, text = run(interview_drill, args + ["--out", victim])
            self.assertEqual(rc, 2, text)
            self.assertEqual(read(victim), before)

    def test_package_refuses_targets_that_overlap_the_source(self):
        src = os.path.join(self.d, "hackerrank-orchestrate")
        shutil.copytree(SKILL, src, ignore=shutil.ignore_patterns("__pycache__"))
        keep = self.path("hackerrank-orchestrate/fixtures/keep.csv", "x\n")
        for args in (["--out", os.path.join(self.d, "dist"), "--install", self.d, "--force"],
                     ["--out", os.path.join(src, "scripts")]):
            rc, text = run(package_skill, ["--skill-dir", src] + args)
            self.assertEqual(rc, 2, text)
        self.assertTrue(os.path.isfile(keep))
        self.assertFalse(os.path.exists(os.path.join(src, "scripts", "hackerrank-orchestrate.zip")))


class SelfcheckConfigPipe(Tmp):
    """Mutation round 3: dropping selfcheck's named-pipe check on config paths passed every
    test, because the matrix only passes a pipe as the config itself."""

    @unittest.skipUnless(hasattr(os, "mkfifo"), "needs named pipes")
    def test_a_pipe_in_the_config_fails_instead_of_hanging(self):
        pipe = os.path.join(self.d, "report.md")
        os.mkfifo(pipe)
        cfg = self.path("c.json", json.dumps({"usage_report": {"path": "report.md"}}))
        proc = subprocess.run([sys.executable, "-I", "-B", os.path.join(SKILL, "scripts", "selfcheck.py"), cfg],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertRegex(proc.stdout, r"usage_report\s+FAIL")


class DryRun(Tmp):
    """The whole loop on the synthetic edition: each step's output is the next step's
    input, exit codes compose, nothing needs the network or an install."""

    def script(self, name, *args, cwd=None):
        proc = subprocess.run([sys.executable, "-I", "-B", os.path.join(SKILL, "scripts", name)] + list(args),
                              capture_output=True, text=True, cwd=cwd, timeout=120)
        return proc.returncode, proc.stdout + proc.stderr

    def test_loop_composes(self):
        proj = os.path.join(self.d, "p")
        shutil.copytree(SYNTH, proj)
        st = os.path.join(proj, "starter")
        rc, text = self.script("contract_extract.py", st, "--out", os.path.join(proj, "notes", "contract.md"))
        self.assertEqual(rc, 0, text)
        self.assertIn("must", read(proj, "notes", "contract.md"))
        common = ["--template", os.path.join(st, "dataset", "output.csv"),
                  "--inputs", os.path.join(st, "dataset", "requests.csv"), "--id-col", "request_id",
                  "--enum", "action=assign|reject|escalate", "--enum", "locker_size=S|M|L|none",
                  "--nonempty", "justification"]
        self.assertEqual(self.script("preflight.py", os.path.join(proj, "runs", "output_v0_flawed.csv"),
                                     *common)[0], 1)
        rc, text = self.script("preflight.py", os.path.join(proj, "runs", "output_v1.csv"), *common)
        self.assertEqual(rc, 0, text)
        rc, text = self.script("rerun_diff.py", os.path.join(proj, "runs", "output_v1.csv"),
                               os.path.join(proj, "runs", "output_v1_rerun.csv"), "--id-col", "request_id",
                               "--ignore", "justification")
        self.assertEqual(rc, 1, text)
        floor = int(re.search(r"rows changed in any compared column: (\d+)", text).group(1))
        self.assertEqual(floor, 1)
        out = os.path.join(proj, "output.csv")
        shutil.copyfile(os.path.join(proj, "runs", "output_v1.csv"), out)
        exp = ["--dir", os.path.join(proj, ".experiments")]
        rc, text = self.script("experiment.py", *exp, "start", "bypass", "--output", out,
                               "--id-col", "request_id", "--labels", os.path.join(st, "dataset", "output.csv"),
                               "--ignore", "justification", "--noise-floor", str(floor), "--check",
                               f'"{sys.executable}" -I "{os.path.join(SKILL, "scripts", "preflight.py")}" "{out}" '
                               + " ".join(f'"{a}"' for a in common))
        self.assertEqual(rc, 0, text)
        shutil.copyfile(os.path.join(proj, "runs", "output_v2.csv"), out)
        rc, text = self.script("experiment.py", *exp, "finish", "bypass",
                               "--record", os.path.join(proj, "docs", "changes.md"))
        self.assertEqual(rc, 4, text)  # one labeled row: NOISE, never SHIP
        self.assertEqual(self.script("check_log.py", os.path.join(proj, "log_good.txt"),
                                     "--expect-tool", "Codex")[0], 0)
        self.assertEqual(self.script("check_log.py", os.path.join(proj, "log_bad.txt"),
                                     "--expect-tool", "Codex")[0], 1)
        rc, text = self.script("usage_report.py", os.path.join(proj, "usage.jsonl"), "--run-id", "final",
                               "--price", "model-a=3:15", "--requests", "12",
                               "--out", os.path.join(proj, "code", "evaluation", "usage_report.md"))
        self.assertEqual(rc, 0, text)
        rc, text = self.script("selfcheck.py", os.path.join(proj, "selfcheck.json"))
        self.assertEqual(rc, 2, text)  # claims is not configured, so the worst result is UNKNOWN
        for name in ("starter", "log", "output", "usage_report", "constants", "corpus_literals"):
            self.assertRegex(text, name + r"\s+PASS", text)
        self.assertRegex(text, r"claims\s+UNKNOWN")
        rc, text = self.script("interview_drill.py", os.path.join(proj, "code"),
                               "--constants", os.path.join(proj, "CONSTANTS.md"))
        self.assertEqual(rc, 0, text)
        self.assertIn("MAX_WEIGHT_KG", text)


if __name__ == "__main__":
    unittest.main()
