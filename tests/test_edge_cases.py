"""Edge cases for every script and tests for the skill validator. Run: python -W error -m unittest discover tests"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SKILL = os.path.join(ROOT, "hackerrank-orchestrate")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check_log  # noqa: E402
import interview_drill  # noqa: E402
import preflight  # noqa: E402
import rerun_diff  # noqa: E402
import usage_report  # noqa: E402
import validate_skill  # noqa: E402


def run(mod, args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = mod.main(args)
    return rc, out.getvalue() + err.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.d = self._d.name

    def tearDown(self):
        self._d.cleanup()

    def write(self, name, text, encoding="utf-8", newline=None):
        p = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding=encoding, newline=newline) as fh:
            fh.write(text)
        return p


GOOD_ENTRY = ("## [{ts}] {title}\n\nUser Prompt (verbatim, secrets redacted):\nhello\n\n"
              "Agent Response Summary:\ndone\n\nContext:\ntool=Claude Code\n\n")
START = "## [{ts}] SESSION START\n\ntool=Claude Code\n\n"


class CheckLogEdges(Tmp):
    def test_crlf_warns_but_passes(self):
        text = START.format(ts="2026-10-24T10:00:00+05:30") + GOOD_ENTRY.format(ts="2026-10-24T10:05:00+05:30", title="t")
        p = self.write("log.txt", text.replace("\n", "\r\n"), newline="")
        rc, out = run(check_log, [p])
        self.assertEqual(rc, 0, out)
        self.assertIn("CRLF", out)

    def test_bom_does_not_hide_first_entry(self):
        text = START.format(ts="2026-10-24T10:00:00Z")
        p = self.write("log.txt", "﻿" + text)
        rc, out = run(check_log, [p])
        self.assertEqual(rc, 0, out)
        self.assertIn("1 entries checked", out)

    def test_empty_file(self):
        rc, out = run(check_log, [self.write("log.txt", "")])
        self.assertEqual(rc, 1)
        self.assertIn("no log entries", out)

    def test_mixed_naive_and_aware_timestamps_warn(self):
        text = START.format(ts="2026-10-24T10:00:00") + GOOD_ENTRY.format(ts="2026-10-24T10:05:00+05:30", title="t")
        rc, out = run(check_log, [self.write("log.txt", text)])
        self.assertEqual(rc, 0, out)
        self.assertIn("mixes timezone-aware and naive", out)

    def test_large_log(self):
        entries = [START.format(ts="2026-10-24T00:00:00+00:00")]
        for i in range(3000):
            entries.append(GOOD_ENTRY.format(ts=f"2026-10-24T{i // 3600:02d}:{i // 60 % 60:02d}:{i % 60:02d}+00:00",
                                             title=f"turn {i}"))
        rc, out = run(check_log, [self.write("log.txt", "".join(entries))])
        self.assertEqual(rc, 0, out[-300:])
        self.assertIn("3001 entries checked", out)

    def test_not_utf8(self):
        p = os.path.join(self.d, "log.txt")
        with open(p, "wb") as fh:
            fh.write(b"## [2026-10-24T10:00:00Z] SESSION START\n\xff\xfe tool=x\n")
        rc, out = run(check_log, [p])
        self.assertEqual(rc, 1)
        self.assertIn("not valid UTF-8", out)


class PreflightEdges(Tmp):
    def args(self, out, extra=()):
        tpl = self.write("tpl.csv", "id,label,note\n")
        inp = self.write("in.csv", "id,x\nü1,a\nü2,b\n")
        return [out, "--template", tpl, "--inputs", inp, "--id-col", "id"] + list(extra)

    def test_unicode_ids_quoted_commas_crlf(self):
        out = self.write("out.csv", 'id,label,note\r\nü1,yes,"a, b"\r\nü2,no,"multi\r\nline"\r\n', newline="")
        rc, text = run(preflight, self.args(out, ["--enum", "label=yes|no"]))
        self.assertEqual(rc, 0, text)

    def test_bom_is_warning(self):
        out = self.write("out.csv", "id,label,note\nü1,yes,a\nü2,no,b\n", encoding="utf-8-sig")
        rc, text = run(preflight, self.args(out))
        self.assertEqual(rc, 0, text)
        self.assertIn("BOM", text)

    def test_duplicate_headers(self):
        out = self.write("out.csv", "id,label,label\nü1,yes,a\nü2,no,b\n")
        rc, text = run(preflight, self.args(out))
        self.assertEqual(rc, 1)
        self.assertIn("duplicate header columns", text)

    def test_empty_output(self):
        rc, text = run(preflight, self.args(self.write("out.csv", "")))
        self.assertEqual(rc, 1)
        self.assertIn("empty", text)

    def test_collapsed_distribution_warns(self):
        out = self.write("out.csv", "id,label,note\nü1,yes,a\nü2,yes,b\n")
        rc, text = run(preflight, self.args(out, ["--enum", "label=yes|no"]))
        self.assertEqual(rc, 0)
        self.assertIn("same label", text)

    def test_large_file(self):
        n = 50000
        tpl = self.write("tpl.csv", "id,label\n")
        inp = self.write("in.csv", "id\n" + "".join(f"r{i}\n" for i in range(n)))
        out = self.write("out.csv", "id,label\n" + "".join(f"r{i},{'yes' if i % 2 else 'no'}\n" for i in range(n)))
        rc, text = run(preflight, [out, "--template", tpl, "--inputs", inp, "--id-col", "id", "--enum", "label=yes|no"])
        self.assertEqual(rc, 0, text)
        self.assertIn(f"{n} rows checked", text)


class RerunDiffEdges(Tmp):
    def test_bom_and_crlf_compare_equal_by_value(self):
        a = self.write("a.csv", "id,v\nr1,1\nr2,2\n")
        b = self.write("b.csv", "﻿id,v\r\nr1,1\r\nr2,2\r\n", newline="")
        rc, out = run(rerun_diff, [a, b, "--id-col", "id"])
        self.assertEqual(rc, 0, out)
        self.assertIn("0 of 2", out)

    def test_duplicate_header_and_id_are_errors(self):
        a = self.write("a.csv", "id,v,v\nr1,1,2\n")
        rc, out = run(rerun_diff, [a, a, "--id-col", "id"])
        self.assertEqual(rc, 2)
        self.assertIn("duplicate columns", out)
        b = self.write("b.csv", "id,v\nr1,1\nr1,2\n")
        rc, out = run(rerun_diff, [b, b, "--id-col", "id"])
        self.assertEqual(rc, 2)
        self.assertIn("duplicate id", out)

    def test_empty_file_is_usage_error(self):
        e = self.write("e.csv", "")
        rc, out = run(rerun_diff, [e, e, "--id-col", "id"])
        self.assertEqual(rc, 2)

    def test_unicode_ids_and_quoted_commas(self):
        a = self.write("a.csv", 'id,v\nü1,"x, y"\n')
        b = self.write("b.csv", 'id,v\nü1,"x, z"\n')
        rc, out = run(rerun_diff, [a, b, "--id-col", "id"])
        self.assertEqual(rc, 1)
        self.assertIn("ü1", out)


class UsageReportEdges(Tmp):
    def test_empty_log(self):
        rc, out = run(usage_report, [self.write("u.jsonl", "")])
        self.assertEqual(rc, 2)
        self.assertIn("no calls found", out)

    def test_bad_json_and_missing_fields(self):
        rc, out = run(usage_report, [self.write("u.jsonl", "{not json}\n")])
        self.assertEqual(rc, 2)
        rc, out = run(usage_report, [self.write("v.jsonl", '{"provider": "p", "model": "m"}\n')])
        self.assertEqual(rc, 2)
        self.assertIn("missing", out)

    def test_crlf_blank_lines_and_unicode_ids(self):
        line = '{"provider": "p", "model": "m", "request_id": "ü1", "input_tokens": 10, "output_tokens": 2}'
        p = self.write("u.jsonl", f"{line}\r\n\r\n{line}\r\n", newline="")
        rc, out = run(usage_report, [p, "--price", "m=1:2"])
        self.assertEqual(rc, 0, out)
        self.assertIn("| Requests processed | 1 |", out)
        self.assertIn("| Model calls | 2 |", out)

    def test_bad_price_spec(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                usage_report.main([self.write("u.jsonl", ""), "--price", "m=abc"])


class InterviewDrillEdges(Tmp):
    def test_syntax_error_file_is_reported_not_fatal(self):
        self.write("code/bad.py", "def x(:\n")
        self.write("code/ok.py", "LIMIT = 7\n")
        rc, out = run(interview_drill, [os.path.join(self.d, "code")])
        self.assertEqual(rc, 0)
        self.assertIn("could not be parsed", out)
        self.assertIn("LIMIT", out)

    def test_bom_crlf_and_unicode_source(self):
        self.write("code/a.py", "﻿SEUIL_É = 0.42\r\nif x > 0.42:\r\n    pass\r\n", newline="")
        findings, consts = interview_drill.scan_paths([os.path.join(self.d, "code")])
        self.assertTrue(any(k == "threshold" for k, *_ in findings))

    def test_include_tests_does_not_leak_between_calls(self):
        self.write("code/tests/test_x.py", "TEST_LIMIT = 9\n")
        root = os.path.join(self.d, "code")
        self.assertEqual(interview_drill.scan_paths([root], include_tests=True)[1], ["TEST_LIMIT"])
        self.assertEqual(interview_drill.scan_paths([root])[1], [])

    def test_empty_directory(self):
        os.makedirs(os.path.join(self.d, "code"))
        rc, out = run(interview_drill, [os.path.join(self.d, "code")])
        self.assertEqual(rc, 3)  # 2.4.0: nothing scanned is UNKNOWN, not a clean drill
        self.assertIn("Always asked", out)
        self.assertIn("UNKNOWN no supported source file", out)


class Validator(Tmp):
    def copy_skill(self):
        dest = os.path.join(self.d, ".claude", "skills", "hackerrank-orchestrate")
        shutil.copytree(SKILL, dest, ignore=shutil.ignore_patterns("__pycache__"))
        return dest

    def errors(self, skill_dir):
        errs = []
        validate_skill.check_skill(skill_dir, errs)
        return errs

    def edit(self, path, old, new):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, new, 1))

    def test_installed_copy_loads_standalone(self):
        dest = self.copy_skill()
        rc, out = run(validate_skill, ["--skill-dir", dest, "--standalone"])
        self.assertEqual(rc, 0, out)

    def test_catches_unlisted_script_and_missing_failure_line(self):
        dest = self.copy_skill()
        self.write(os.path.join(dest, "scripts", "extra.py"), '"""Docstring only."""\nimport sys\nsys.exit(0)\n')
        errs = "\n".join(self.errors(dest))
        self.assertIn("scripts/extra.py is not listed", errs)
        self.assertIn("must name the failure", errs)

    def test_catches_dated_description_and_missing_do_not_use(self):
        dest = self.copy_skill()
        md = os.path.join(dest, "SKILL.md")
        self.edit(md, "Do not use for general prompt writing", "Avoid general prompt writing in 2026")
        errs = "\n".join(self.errors(dest))
        self.assertIn("contains a date", errs)
        self.assertIn("'Do not use for ...' clause", errs)

    def test_catches_restated_rule_and_gap_in_numbering(self):
        dest = self.copy_skill()
        self.edit(os.path.join(dest, "references", "evaluation.md"), "# Evaluation and anti-overfitting",
                  "# Evaluation and anti-overfitting\n\nOne labeled row is noise.")
        self.edit(os.path.join(dest, "SKILL.md"), "\n5. **Choose the grouping", "\n6. **Choose the grouping")
        errs = "\n".join(self.errors(dest))
        self.assertIn("hard rule 4 is restated verbatim", errs)
        self.assertIn("numbered 1..N contiguously", errs)

    def test_every_shipped_profile_has_a_provenance_label(self):
        for fn in sorted(os.listdir(os.path.join(SKILL, "assets", "editions"))):
            with open(os.path.join(SKILL, "assets", "editions", fn), encoding="utf-8") as fh:
                prof = json.load(fh)
            self.assertIn(prof.get("provenance"), validate_skill.PROVENANCE_LABELS, fn)
            self.assertTrue(prof.get("provenance_source", "").strip(), fn)

    def test_catches_missing_or_bad_profile_provenance(self):
        dest = self.copy_skill()
        june = os.path.join(dest, "assets", "editions", "june-2026.json")
        self.edit(june, '"provenance": "VERIFIED"', '"provenance": "PROBABLY"')
        sept = os.path.join(dest, "assets", "editions", "sept-2026.json")
        with open(sept, encoding="utf-8") as fh:
            prof = json.load(fh)
        del prof["provenance"]
        prof["provenance_source"] = " "
        with open(sept, "w", encoding="utf-8") as fh:
            json.dump(prof, fh)
        errs = "\n".join(self.errors(dest))
        self.assertIn("june-2026.json: provenance must be one of", errs)
        self.assertIn("sept-2026.json lacks keys ['provenance']", errs)
        self.assertIn("sept-2026.json: provenance_source is empty", errs)

    def test_catches_long_reference_without_contents_and_bad_archetype(self):
        dest = self.copy_skill()
        self.write(os.path.join(dest, "references", "long.md"), "# Long\n" + "line\n" * 120)
        self.write(os.path.join(dest, "references", "archetypes", "new-shape.md"), "# New\n## Guards that fit\n")
        errs = "\n".join(self.errors(dest))
        self.assertIn("long.md is 121 lines", errs)
        self.assertIn("new-shape.md lacks a '## Architecture that held up'", errs)

    def test_catches_readme_inside_skill_and_missing_reference(self):
        dest = self.copy_skill()
        self.write(os.path.join(dest, "README.md"), "# no\n")
        self.edit(os.path.join(dest, "SKILL.md"), "`references/rubric.md`", "`references/rubrik.md`")
        errs = "\n".join(self.errors(dest))
        self.assertIn("must not contain README.md", errs)
        self.assertIn("references missing path references/rubrik.md", errs)

    def test_personal_marker_pattern(self):
        samples = ["global " + "#51", "scored 70.7" + "/100", "Ranked " + "#3"]  # split so the repo scan stays clean
        hits = [bool(rx.search(t)) for t in samples
                for rx in validate_skill.PERSONAL_MARKERS]
        self.assertGreaterEqual(sum(hits), 3)
        self.assertFalse(any(rx.search("one 0–100 safety score") for rx in validate_skill.PERSONAL_MARKERS))


if __name__ == "__main__":
    unittest.main()
