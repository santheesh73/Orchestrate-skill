"""Tests for the repo tools: packaging, footprint budgets and the coverage matrix."""

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SKILL = os.path.join(ROOT, "hackerrank-orchestrate")
sys.path.insert(0, os.path.join(ROOT, "tools"))

import footprint  # noqa: E402
import package_skill  # noqa: E402
import validate_skill  # noqa: E402


def run(mod, args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = mod.main(args)
        except SystemExit as exc:
            rc = exc.code
    return rc, out.getvalue()


class Package(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)

    def copy_skill_with_junk(self):
        src = os.path.join(self.d, "src", "hackerrank-orchestrate")
        shutil.copytree(SKILL, src, ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(src, "scripts", "__pycache__"))
        for junk in ("scripts/__pycache__/x.cpython-311.pyc", "scripts/stray.pyc", ".DS_Store",
                     "tests/test_x.py", "assets/fixtures/sample.csv"):
            p = os.path.join(src, junk)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write("junk\n")
        return src

    def test_zip_has_one_top_folder_with_skill_md_and_no_dev_files(self):
        src = self.copy_skill_with_junk()
        out = os.path.join(self.d, "dist")
        rc, text = run(package_skill, ["--skill-dir", src, "--out", out])
        self.assertEqual(rc, 0, text)
        with zipfile.ZipFile(os.path.join(out, "hackerrank-orchestrate.zip")) as zf:
            names = zf.namelist()
        self.assertEqual({n.split("/")[0] for n in names}, {"hackerrank-orchestrate"})
        self.assertIn("hackerrank-orchestrate/SKILL.md", names)
        self.assertIn("hackerrank-orchestrate/scripts/selfcheck.py", names)
        bad = [n for n in names if re.search(r"__pycache__|\.pyc$|\.DS_Store|/tests/|/fixtures/", n)]
        self.assertEqual(bad, [])

    def test_install_refuses_to_overwrite_without_force(self):
        out, inst = os.path.join(self.d, "dist"), os.path.join(self.d, "skills")
        self.assertEqual(run(package_skill, ["--out", out, "--install", inst])[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(inst, "hackerrank-orchestrate", "SKILL.md")))
        self.assertEqual(run(package_skill, ["--out", out, "--install", inst])[0], 2)
        self.assertEqual(run(package_skill, ["--out", out, "--install", inst, "--force"])[0], 0)
        rc, text = run(validate_skill, ["--skill-dir", os.path.join(inst, "hackerrank-orchestrate"), "--standalone"])
        self.assertEqual(rc, 0, text)

    def test_invalid_skill_is_not_packaged(self):
        src = self.copy_skill_with_junk()
        md = os.path.join(src, "SKILL.md")
        with open(md, encoding="utf-8") as fh:
            text = fh.read()
        with open(md, "w", encoding="utf-8") as fh:
            fh.write(text.replace("Do not use for", "Avoid for", 1))
        out = os.path.join(self.d, "dist")
        rc, text = run(package_skill, ["--skill-dir", src, "--out", out])
        self.assertEqual(rc, 1)
        self.assertIn("'Do not use for ...' clause", text)
        self.assertFalse(os.path.exists(os.path.join(out, "hackerrank-orchestrate.zip")))


class Footprint(unittest.TestCase):
    def test_current_skill_is_within_budget(self):
        parts, files = footprint.measure(SKILL)
        self.assertEqual(footprint.over_budget(parts), [])
        self.assertEqual(parts["always_loaded"], parts["description"] + parts["skill_body"])
        self.assertIn("SKILL.md", [f[0] for f in files])
        self.assertEqual(run(footprint, ["--summary"])[0], 0)

    def test_growth_past_budget_is_reported_by_tool_and_validator(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        dest = os.path.join(d, "hackerrank-orchestrate")
        shutil.copytree(SKILL, dest, ignore=shutil.ignore_patterns("__pycache__"))
        md = os.path.join(dest, "SKILL.md")
        with open(md, "a", encoding="utf-8") as fh:
            fh.write("x" * 2000 + "\n")
        rc, text = run(footprint, ["--skill-dir", dest, "--summary"])
        self.assertEqual(rc, 1)
        self.assertIn("OVER BUDGET skill_body", text)
        errs = []
        validate_skill.check_skill(dest, errs)
        self.assertTrue(any("footprint: always_loaded" in e for e in errs), errs)

    def test_estimate_is_chars_over_four_rounded_up(self):
        self.assertEqual([footprint.est_tokens(n) for n in (0, 1, 4, 5)], [0, 1, 1, 2])


class RulesHaveOneCopy(unittest.TestCase):
    def test_readme_restating_a_hard_rule_is_an_error(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        os.makedirs(os.path.join(d, "hackerrank-orchestrate"))
        shutil.copy(os.path.join(SKILL, "SKILL.md"), os.path.join(d, "hackerrank-orchestrate", "SKILL.md"))
        titles = validate_skill.hard_rule_titles(os.path.join(SKILL, "SKILL.md"))
        self.assertEqual(len(titles), 14)
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("Guide\n\n- **%s.** Restated.\n" % titles[10])
        errs = []
        validate_skill.check_docs_restate_no_rules(d, errs)
        self.assertEqual(errs, ["hard rule 11 is restated verbatim in README.md; link instead"])
        errs = []
        validate_skill.check_docs_restate_no_rules(ROOT, errs)
        self.assertEqual(errs, [])


class Coverage(unittest.TestCase):
    PATH = os.path.join(ROOT, "docs", "COVERAGE.md")

    def test_every_referenced_path_exists(self):
        with open(self.PATH, encoding="utf-8") as fh:
            text = fh.read()
        refs = sorted(set(re.findall(r"`((?:hackerrank-orchestrate|tools|tests|evals|docs)/[^`#\s]+)", text)))
        self.assertGreater(len(refs), 20)
        missing = [r for r in refs if not os.path.exists(os.path.join(ROOT, r))]
        self.assertEqual(missing, [])

    def test_every_rubric_sub_criterion_and_loop_capability_has_a_row(self):
        with open(self.PATH, encoding="utf-8") as fh:
            text = fh.read().lower()
        for item in ("agent architecture", "prompt and tool craft", "robustness", "engineering rigor",
                     "accuracy", "safety score", "technical depth", "judgment", "communication", "honesty",
                     "direction and architecture ownership", "technical specificity", "iteration and verification",
                     "safety, edge case", "agent loop", "rubric context", "compliance trap", "prompt templates",
                     "winning approaches", "toolkit digest", "hard rules", "lessons", "deliberately not ported"):
            self.assertIn(item, text)
        self.assertNotIn("| none |", text)


if __name__ == "__main__":
    unittest.main()
