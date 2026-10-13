"""Tests for the repo tools: packaging, footprint budgets and the coverage matrix."""

import contextlib
import io
import os
import re
import shutil
import subprocess
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


class HostileSkillFolders(unittest.TestCase):
    """Adversarial round 3: a non-UTF-8 SKILL.md or a broken symlink in the skill crashed the
    validator and packager, and --out or --install pointing at a file raised tracebacks."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.skill = os.path.join(self.d, "hackerrank-orchestrate")
        shutil.copytree(SKILL, self.skill, ignore=shutil.ignore_patterns("__pycache__"))

    def test_non_utf8_skill_md_is_an_error_not_a_crash(self):
        with open(os.path.join(self.skill, "SKILL.md"), "wb") as fh:
            fh.write(b"\xff\xfe---\n")
        rc, text = run(validate_skill, ["--skill-dir", self.skill, "--standalone"])
        self.assertEqual(rc, 1)
        self.assertIn("SKILL.md is not valid UTF-8", text)
        self.assertEqual(run(package_skill, ["--skill-dir", self.skill, "--out", os.path.join(self.d, "o")])[0], 1)
        self.assertEqual(run(footprint, ["--skill-dir", self.skill])[0], 2)

    @unittest.skipUnless(hasattr(os, "symlink"), "needs symlinks")
    def test_broken_symlink_is_reported_and_not_packaged(self):
        try:
            os.symlink(os.path.join(self.d, "gone.md"), os.path.join(self.skill, "references", "gone.md"))
        except OSError:
            self.skipTest("symlinks not permitted here")
        rc, text = run(validate_skill, ["--skill-dir", self.skill, "--standalone"])
        self.assertEqual(rc, 1)
        self.assertIn("references/gone.md is a broken symlink", text.replace(os.sep, "/"))
        self.assertEqual(run(footprint, ["--skill-dir", self.skill, "--summary"])[0], 0)
        out = os.path.join(self.d, "o")
        self.assertEqual(run(package_skill, ["--skill-dir", self.skill, "--out", out])[0], 0)
        with zipfile.ZipFile(os.path.join(out, "hackerrank-orchestrate.zip")) as zf:
            self.assertNotIn("hackerrank-orchestrate/references/gone.md", zf.namelist())

    def test_out_or_install_onto_a_file_is_a_usage_error(self):
        blocker = os.path.join(self.d, "blocker")
        with open(blocker, "w") as fh:
            fh.write("x")
        rc, text = run(package_skill, ["--out", blocker])
        self.assertEqual(rc, 2)
        self.assertIn("cannot write", text)
        rc, text = run(package_skill, ["--out", os.path.join(self.d, "o"), "--install", blocker])
        self.assertEqual(rc, 2)
        self.assertIn("cannot install", text)



class AtomicInstall(unittest.TestCase):
    """v2.2.1 (D5): --install --force deleted the installed copy before copying the new one,
    so a failed copy left the user with no skill at all."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.inst = os.path.join(self.d, "skills")
        self.target = os.path.join(self.inst, "hackerrank-orchestrate")
        os.makedirs(self.target)
        with open(os.path.join(self.target, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("OLD COPY\n")

    def old_copy_intact(self):
        with open(os.path.join(self.target, "SKILL.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "OLD COPY\n")
        self.assertEqual(sorted(os.listdir(self.inst)), ["hackerrank-orchestrate"])  # no temp debris

    def install(self, *extra):
        return run(package_skill, ["--out", os.path.join(self.d, "dist"), "--install", self.inst] + list(extra))

    def test_failure_mid_copy_keeps_the_old_copy(self):
        real = shutil.copytree

        def broken(src, dst, *a, **k):
            if dst.startswith(self.inst):
                os.makedirs(dst)
                with open(os.path.join(dst, "SKILL.md"), "w") as fh:
                    fh.write("half")
                raise OSError(28, "No space left on device")
            return real(src, dst, *a, **k)

        package_skill.shutil.copytree = broken
        try:
            rc, text = self.install("--force")
        finally:
            package_skill.shutil.copytree = real
        self.assertEqual(rc, 2, text)
        self.assertIn("cannot install", text)
        self.old_copy_intact()

    def test_failure_at_the_swap_restores_the_old_copy(self):
        real, calls = os.rename, []

        def flaky(src, dst):
            calls.append((src, dst))
            if len(calls) == 2:  # moving the new copy into place
                raise OSError(13, "Permission denied")
            return real(src, dst)

        package_skill.os.rename = flaky
        try:
            rc, text = self.install("--force")
        finally:
            package_skill.os.rename = real
        self.assertEqual(rc, 2, text)
        self.old_copy_intact()

    def test_force_replaces_and_leaves_no_debris(self):
        self.assertEqual(self.install()[0], 2)
        self.old_copy_intact()
        rc, text = self.install("--force")
        self.assertEqual(rc, 0, text)
        self.assertEqual(sorted(os.listdir(self.inst)), ["hackerrank-orchestrate"])
        rc, text = run(validate_skill, ["--skill-dir", self.target, "--standalone"])
        self.assertEqual(rc, 0, text)

    def test_target_that_is_a_file(self):
        shutil.rmtree(self.target)
        with open(self.target, "w") as fh:
            fh.write("a file")
        self.assertEqual(self.install()[0], 2)
        self.assertTrue(os.path.isfile(self.target))
        self.assertEqual(self.install("--force")[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "SKILL.md")))

    @unittest.skipUnless(hasattr(os, "symlink"), "needs symlinks")
    def test_target_that_is_a_symlink_is_replaced_not_followed(self):
        elsewhere = os.path.join(self.d, "elsewhere")
        os.rename(self.target, elsewhere)
        try:
            os.symlink(elsewhere, self.target)
        except OSError:
            self.skipTest("symlinks not permitted here")
        self.assertEqual(self.install()[0], 2)
        self.assertEqual(self.install("--force")[0], 0)
        self.assertFalse(os.path.islink(self.target))
        with open(os.path.join(elsewhere, "SKILL.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "OLD COPY\n")  # the link's target was not touched


class InstallDocChecks(unittest.TestCase):
    """v2.3.0: docs/INSTALL.md must cover the six agents; SKILL.md body names no install folder."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)

    def test_install_doc_missing_or_incomplete(self):
        errs = []
        validate_skill.check_install_doc(self.d, errs)
        self.assertEqual(errs, ["docs/INSTALL.md is missing"])
        os.makedirs(os.path.join(self.d, "docs"))
        with open(os.path.join(self.d, "docs", "INSTALL.md"), "w", encoding="utf-8") as fh:
            fh.write("Claude Code, Claude.ai, Codex, OpenCode and Cursor.\n")
        errs = []
        validate_skill.check_install_doc(self.d, errs)
        self.assertEqual(errs, ["docs/INSTALL.md does not name Antigravity"])
        errs = []
        validate_skill.check_install_doc(ROOT, errs)
        self.assertEqual(errs, [])

    def test_agent_install_path_in_skill_body_is_an_error(self):
        skill = os.path.join(self.d, "hackerrank-orchestrate")
        shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns("__pycache__"))
        with open(os.path.join(skill, "SKILL.md"), "a", encoding="utf-8") as fh:
            fh.write("\nInstall it under `~/.gemini/config/skills/` for Antigravity.\n")
        errs = []
        validate_skill.check_skill(skill, errs)
        self.assertEqual([e for e in errs if "install path" in e],
                         ["SKILL.md body names the agent-specific install path '.gemini/config'; "
                          "install folders belong in docs/INSTALL.md"])


class ProjectInstall(unittest.TestCase):
    """v2.3.0: --project DIR --for {claude,agents,all} installs into a project's skill folders."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.project = os.path.join(self.d, "entry")
        os.makedirs(self.project)

    def target(self, layout):
        return os.path.join(self.project, layout, "skills", "hackerrank-orchestrate")

    def install(self, *extra):
        return run(package_skill, ["--out", os.path.join(self.d, "dist"), "--project", self.project] + list(extra))

    def tree(self, top):
        files = {}
        for path, rel in package_skill.skill_files(top):
            with open(path, "rb") as fh:
                files[rel] = fh.read()
        return files

    def test_each_layout_installs_only_its_folder(self):
        for layout, present in (("claude", ".claude"), ("agents", ".agents")):
            with self.subTest(layout=layout):
                shutil.rmtree(self.project)
                os.makedirs(self.project)
                rc, text = self.install("--for", layout)
                self.assertEqual(rc, 0, text)
                self.assertEqual(os.listdir(self.project), [present])
                self.assertTrue(os.path.isfile(os.path.join(self.target(present), "SKILL.md")))

    def test_all_installs_two_identical_copies(self):
        rc, text = self.install()  # --for defaults to all
        self.assertEqual(rc, 0, text)
        claude, agents = self.tree(self.target(".claude")), self.tree(self.target(".agents"))
        self.assertIn("SKILL.md", claude)
        self.assertEqual(claude, agents)
        # v2.3.0 defect: validating the installed copy ran each script's --help without -B,
        # which wrote __pycache__ into every installed skill.
        for layout in (".claude", ".agents"):
            self.assertFalse([dp for dp, _, _ in os.walk(self.target(layout)) if "__pycache__" in dp])

    def test_existing_target_without_force_installs_nothing(self):
        os.makedirs(self.target(".agents"))
        rc, text = self.install("--for", "all")
        self.assertEqual(rc, 2, text)
        self.assertIn("pass --force", text)
        self.assertFalse(os.path.exists(os.path.join(self.project, ".claude")))
        self.assertEqual(os.listdir(self.target(".agents")), [])
        self.assertEqual(self.install("--for", "all", "--force")[0], 0)

    def test_failure_mid_copy_keeps_the_old_copy(self):
        os.makedirs(self.target(".agents"))
        with open(os.path.join(self.target(".agents"), "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("OLD COPY\n")
        real = shutil.copytree
        skills = os.path.join(self.project, ".agents", "skills")

        def broken(src, dst, *a, **k):
            if dst.startswith(skills):
                os.makedirs(dst)
                raise OSError(28, "No space left on device")
            return real(src, dst, *a, **k)

        package_skill.shutil.copytree = broken
        try:
            rc, text = self.install("--for", "agents", "--force")
        finally:
            package_skill.shutil.copytree = real
        self.assertEqual(rc, 2, text)
        with open(os.path.join(self.target(".agents"), "SKILL.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "OLD COPY\n")
        self.assertEqual(os.listdir(skills), ["hackerrank-orchestrate"])  # no temp debris

    def test_usage_errors(self):
        self.assertEqual(run(package_skill, ["--for", "all"])[0], 2)
        self.assertEqual(run(package_skill, ["--project", os.path.join(self.d, "missing")])[0], 2)
        self.assertEqual(self.install("--for", "codex")[0], 2)


class PortabilitySmoke(unittest.TestCase):
    """v2.3.0: an installed copy, in either layout, validates and runs on its own.

    Each check is a fresh `python -I -B` process (no user site, no cwd on sys.path, no
    __pycache__ written into the installed folder; -I ignores PYTHONDONTWRITEBYTECODE) with the
    proxy variables pointed at a closed port, so a script that reached for the network or
    for a file in this repo would fail here.
    """

    def test_installed_copy_validates_and_every_script_answers_help(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        rc, text = run(package_skill, ["--out", os.path.join(d, "dist"), "--project", d, "--for", "all"])
        self.assertEqual(rc, 0, text)
        env = dict(os.environ)
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"):
            env[var] = "http://127.0.0.1:9"
        for layout in (".claude", ".agents"):
            installed = os.path.join(d, layout, "skills", "hackerrank-orchestrate")
            jobs = [[os.path.join(ROOT, "tools", "validate_skill.py"), "--standalone", "--skill-dir", installed]]
            scripts = os.path.join(installed, "scripts")
            names = sorted(f for f in os.listdir(scripts) if f.endswith(".py"))
            self.assertGreaterEqual(len(names), 9)
            jobs += [[os.path.join(scripts, f), "--help"] for f in names]
            for job in jobs:
                with self.subTest(layout=layout, job=os.path.basename(job[0])):
                    proc = subprocess.run([sys.executable, "-I", "-B", "-W", "error"] + job, cwd=d, env=env,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          universal_newlines=True, timeout=60)
                    self.assertEqual(proc.returncode, 0, proc.stdout)
                    self.assertNotIn("Traceback", proc.stdout)
            self.assertFalse(any("__pycache__" in dp for dp, _, _ in os.walk(installed)))


if __name__ == "__main__":
    unittest.main()
