"""Hostile-input regressions: each test reproduces a bug found by feeding the scripts bad input."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "hackerrank-orchestrate", "scripts"))

import claim_audit  # noqa: E402
import preflight  # noqa: E402
import rerun_diff  # noqa: E402
import corpus_literals  # noqa: E402
import interview_drill  # noqa: E402
import selfcheck  # noqa: E402
import usage_report  # noqa: E402

BINARY = bytes(range(256)) * 4
LATIN1_CSV = "id,name\n1,café\n2,naïve\n".encode("latin-1")
# A test file whose source triggers SyntaxWarning (invalid escape) when parsed.
WARNY_TEST = 'import re\nPAT = "\\d+\\."\ndef test_one():\n    pass\ndef test_two():\n    pass\n'


def run(mod, args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(args)
        except SystemExit as exc:
            rc = exc.code
    return rc, out.getvalue() + err.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.d = self._d.name

    def tearDown(self):
        self._d.cleanup()

    def path(self, name, data):
        p = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        return p


class NonUtf8Inputs(Tmp):
    """Round 1: four scripts raised UnicodeDecodeError tracebacks instead of a usage error."""

    def test_usage_report_binary_log_is_a_usage_error(self):
        rc, out = run(usage_report, [self.path("u.jsonl", BINARY), "--price", "m=1:2"])
        self.assertEqual(rc, 2)
        self.assertIn("not valid UTF-8", out)

    def test_interview_drill_binary_constants_is_a_usage_error(self):
        code = self.path("code/a.py", "LIMIT = 5\n")
        rc, out = run(interview_drill, [os.path.dirname(code), "--constants", self.path("c.md", BINARY)])
        self.assertEqual(rc, 2)
        self.assertIn("not valid UTF-8", out)

    def test_claim_audit_latin1_csv_and_constants_are_usage_errors(self):
        doc = self.path("README.md", "3 rows\n")
        for flag in ("--csv", "--constants"):
            rc, out = run(claim_audit, [doc, flag, self.path("x.csv", LATIN1_CSV)])
            self.assertEqual(rc, 2, flag)
            self.assertIn("not valid UTF-8", out)
        rc, out = run(claim_audit, [self.path("bin.md", BINARY), "--repo", self.d])
        self.assertEqual(rc, 0)  # docs are read leniently: a stray byte must not stop the audit

    def test_corpus_literals_binary_allowlist_is_a_usage_error(self):
        data = self.path("d.csv", "id,v\nabc123,1\n")
        code = self.path("c.py", "X = 1\n")
        rc, out = run(corpus_literals, ["--data", data, "--code", code, "--allowlist", self.path("a.txt", BINARY)])
        self.assertEqual(rc, 2)
        self.assertIn("not valid UTF-8", out)


class SelfcheckConfigShapes(Tmp):
    """Round 1: a section that is not an object crashed with AttributeError; a string where a
    list belongs was iterated character by character."""

    def cfg(self, obj):
        return self.path("selfcheck.json", json.dumps(obj))

    def test_section_that_is_not_an_object_is_a_config_error(self):
        rc, out = run(selfcheck, [self.cfg({"log": "log.txt"})])
        self.assertEqual(rc, 4)
        self.assertIn("section 'log' must be a JSON object", out)

    def test_string_where_a_list_belongs_is_a_config_error(self):
        rc, out = run(selfcheck, [self.cfg({"claims": {"docs": "README.md"}})])
        self.assertEqual(rc, 4)
        self.assertIn("claims.docs must be a list of strings", out)

    def test_windows_style_relative_paths_resolve(self):
        self.path("sub/output.csv", "id,status\n1,ok\n")
        self.path("sub/template.csv", "id,status\n")
        rc, out = run(selfcheck, [self.cfg({"output": {"path": "sub\\output.csv", "template": "sub\\template.csv"}})])
        self.assertRegex(out, r"output\s+PASS")


class ParserWarnings(Tmp):
    """Round 1: parsing a participant's file with an invalid escape leaked a SyntaxWarning into
    selfcheck's summary line, and under -W error the file's tests were silently not counted."""

    def test_claim_audit_counts_tests_in_files_that_warn(self):
        self.path("tests/test_x.py", WARNY_TEST)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertEqual(claim_audit.count_tests(self.d), 2)

    def test_no_warning_text_reaches_selfcheck_summary(self):
        self.path("tests/test_x.py", WARNY_TEST)
        self.path("README.md", "2 tests\n")
        cfg = self.path("selfcheck.json", json.dumps({"claims": {"docs": ["README.md"], "repo": "."}}))
        rc, out = run(selfcheck, [cfg])
        self.assertNotIn("SyntaxWarning", out)
        self.assertRegex(out, r"claims\s+PASS\s+1 claims, 0 mismatches")

    def test_drill_and_literals_parse_files_that_warn(self):
        p = self.path("code/m.py", WARNY_TEST + "LIMIT = 7\n")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            _, names = interview_drill.scan_paths([os.path.dirname(p)])
            strings, _ = corpus_literals.python_literals(p)
        self.assertIn("LIMIT", names)
        self.assertTrue(strings)


class CsvShapes(Tmp):
    """Round 2: classic-Mac line endings (CR only) and one field over the csv module's
    131072-character default limit raised csv.Error tracebacks in every CSV reader."""

    CR = "id,status\r1,ok\r2,ok\r"
    LONG = "id,status\n1," + "a" * 200000 + "\n2,ok\n"

    def test_cr_only_and_long_fields_parse_in_every_reader(self):
        for name, text in (("cr.csv", self.CR), ("long.csv", self.LONG)):
            p = self.path(name, text)
            rows, _ = preflight.read_csv(p)
            self.assertEqual(len(rows), 3, name)
            self.assertEqual(len(rerun_diff.load(p, "id")[1]), 2, name)
            self.assertEqual(claim_audit.count_csv_rows(p), 2, name)
            self.assertEqual(len(corpus_literals.read_csv(p)[1]), 2, name)

    def test_cr_only_output_passes_preflight(self):
        out = self.path("o.csv", self.CR)
        rc, text = run(preflight, [out, "--columns", "id,status", "--enum", "status=ok"])
        self.assertEqual(rc, 0, text)
        self.assertIn("2 rows checked", text)

    def test_nul_byte_is_never_a_traceback(self):
        """Python 3.9's csv module rejects NUL bytes; later versions accept them."""
        nul = self.path("nul.csv", "id,status\n1,o\x00k\n")
        other = self.path("ok.csv", "id,status\n1,ok\n")
        for mod, args in ((preflight, [nul, "--columns", "id,status"]),
                          (rerun_diff, ["--id-col", "id", nul, other]),
                          (claim_audit, [other, "--csv", nul]),
                          (corpus_literals, ["--data", nul, "--code", other])):
            rc, text = run(mod, args)
            self.assertIn(rc, (0, 1, 2), mod.__name__)
            if sys.version_info < (3, 10):
                self.assertIn("not parseable as CSV", text, mod.__name__)


@unittest.skipUnless(hasattr(os, "symlink"), "needs symlinks")
class DanglingSymlinks(Tmp):
    """Round 2: a dangling symlink in a participant's code folder (a moved file, a stale
    venv link) crashed interview_drill and stopped corpus_literals and claim_audit."""

    def setUp(self):
        super().setUp()
        self.code = os.path.dirname(self.path("code/a.py", "LIMIT = 5\n"))
        try:
            os.symlink(os.path.join(self.d, "gone.py"), os.path.join(self.code, "dangling.py"))
            os.symlink(os.path.join(self.d, "gone.py"), os.path.join(self.code, "test_gone.py"))
        except OSError:
            self.skipTest("symlinks not permitted here")

    def test_scanners_skip_dangling_links(self):
        _, names = interview_drill.scan_paths([self.code])
        self.assertIn("LIMIT", names)
        data = self.path("d.csv", "id,v\nabc123,1\n")
        rc, text = run(corpus_literals, ["--data", data, "--code", self.code])
        self.assertEqual(rc, 0, text)
        self.assertEqual(claim_audit.count_tests(self.code), 0)


if __name__ == "__main__":
    unittest.main()
