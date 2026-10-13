"""Tests for scripts/experiment.py: the resolution table, the start/finish loop, hostile input."""

import contextlib
import hashlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SKILL = os.path.join(ROOT, "hackerrank-orchestrate")
SYNTH = os.path.join(HERE, "fixtures", "edition_synth")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import experiment  # noqa: E402

PY = sys.executable

# One case per situation the table in references/evaluation.md section 4 covers. Columns:
# table row, checks before, checks after, labeled rows, better, worse, accounted for,
# noise floor, expected verdict.
TABLE_CASES = [
    ("A", [0], [1], 4, ["r1", "r2", "r3"], [], [], 1, "REJECT"),          # regressed, labeled up
    ("A", [0], [1], 4, [], ["r1"], [], 1, "REJECT"),                      # regressed, labeled down
    ("A", [1], [1], 4, ["r1", "r2", "r3"], [], [], 1, "REJECT"),          # red before and after: hard gate
    ("A", [0], [1], 0, [], [], [], 1, "REJECT"),                          # first match: A before B
    ("B", [], [], 4, ["r1", "r2", "r3"], [], [], 1, "UNKNOWN"),           # no label-free check run
    ("B", [0], [0], 0, [], [], [], 1, "UNKNOWN"),                         # no labeled row compared
    ("C", [0], [0], 6, ["r1", "r2", "r3"], ["r4", "r5"], [], 1, "REJECT"),  # mixed +3/-2, unexplained
    ("C", [0], [0], 9, ["r1"], ["r4", "r5", "r6"], ["r4"], 1, "REJECT"),  # two of three worse unexplained
    ("D", [0], [0], 6, [], ["r4", "r5"], ["r4"], 1, "NOISE"),             # one unexplained worse row: rule 4
    ("D", [0], [0], 6, [], ["r4", "r5"], ["r4", "r5"], 1, "NOISE"),       # down 2, both explained
    ("D", [0], [0], 4, [], ["r1"], [], 1, "NOISE"),                       # down 1 row
    ("D", [0], [0], 4, [], [], [], 1, "NOISE"),                           # nothing moved
    ("D", [0], [0], 4, ["r1"], [], [], None, "NOISE"),                    # up 1 row: never SHIP
    ("D", [0], [0], 6, ["r1", "r2"], [], [], 2, "NOISE"),                 # up 2, floor 2: inside noise
    ("D", [0], [0], 6, ["r1", "r2", "r3"], ["r4"], [], 2, "NOISE"),       # net +2, floor 2
    ("E", [0], [0], 4, ["r1", "r2"], [], [], None, "SHIP"),               # up 2, floor unmeasured -> 1
    ("E", [0], [0], 6, ["r1", "r2", "r3"], [], [], 2, "SHIP"),            # up 3 above floor 2
    ("E", [0], [0], 9, ["r1", "r2", "r3", "r6", "r7"], ["r4", "r5"], ["r4", "r5"], 1, "SHIP"),
    ("E", [0], [0], 6, ["r1", "r2", "r3"], ["r4"], [], 1, "SHIP"),        # one worse row is noise
]


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = experiment.main(argv)
        except SystemExit as exc:
            rc = exc.code
    return rc, out.getvalue()


class ResolutionTable(unittest.TestCase):
    """v2.4.0 audit: two readers of the table reached different verdicts for a one-row gain
    (row "Clean | Up -> Keep" against "never accept on a one-row difference") and for a
    mixed change (+3 better / -2 worse: net Up, but hard rule 4 counts the 2 worse rows)."""

    def test_every_case_gets_the_tabled_verdict(self):
        for row, cb, ca, n, better, worse, acc, floor, want in TABLE_CASES:
            with self.subTest(row=row, better=better, worse=worse, floor=floor):
                got, reason = experiment.resolve(cb, ca, n, better, worse, acc, floor)
                self.assertEqual(got, want, reason)
                self.assertTrue(reason)

    def test_same_inputs_same_verdict(self):
        for case in TABLE_CASES:
            args = case[1:8]
            self.assertEqual(experiment.resolve(*args), experiment.resolve(*args))

    def test_every_table_row_has_cases_and_the_table_names_every_verdict(self):
        with open(os.path.join(SKILL, "references", "evaluation.md"), encoding="utf-8") as fh:
            text = fh.read()
        section = text.split("## 4. Resolution table", 1)[1].split("\n## ", 1)[0]
        rows = re.findall(r"^\| ([A-Z]) \|(.*)\|$", section, re.M)
        self.assertEqual([r for r, _ in rows], ["A", "B", "C", "D", "E"])
        for letter, body in rows:
            wanted = {c[8] for c in TABLE_CASES if c[0] == letter}
            self.assertEqual(len(wanted), 1, letter)
            self.assertIn(wanted.pop(), body, f"table row {letter} names another verdict")

    def test_a_one_row_gain_is_never_ship(self):
        for floor in (None, 0, 1, 5):
            self.assertNotEqual(experiment.resolve([0], [0], 9, ["r1"], [], [], floor)[0], "SHIP")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class ExperimentLoop(unittest.TestCase):
    """The change-record loop on the synthetic edition, end to end, with no network."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.proj = os.path.join(self.d, "proj")
        shutil.copytree(SYNTH, self.proj)
        self.out = os.path.join(self.proj, "output.csv")
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v1.csv"), self.out)
        self.exp = os.path.join(self.d, "exps")
        pre = os.path.join(SKILL, "scripts", "preflight.py")
        self.check = (f'"{PY}" -I "{pre}" "{self.out}" --template "{self.proj}/starter/dataset/output.csv" '
                      f'--inputs "{self.proj}/starter/dataset/requests.csv" --id-col request_id '
                      '--enum "action=assign|reject|escalate" --nonempty justification')

    def start(self, *extra):
        return run(["--dir", self.exp, "start", "e1", "--output", self.out, "--id-col", "request_id",
                    "--check", self.check, "--ignore", "justification"] + list(extra))

    def finish(self, *extra):
        return run(["--dir", self.exp, "finish", "e1"] + list(extra))

    def labels(self, rows):
        p = os.path.join(self.d, "labels.csv")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("request_id,action,locker_size\n" + "".join(f"{r}\n" for r in rows))
        return p

    def test_one_row_gain_is_noise_and_the_record_is_complete(self):
        rc, text = self.start("--labels", os.path.join(self.proj, "starter", "dataset", "output.csv"),
                              "--noise-floor", "1")
        self.assertEqual(rc, 0, text)
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v2.csv"), self.out)
        record = os.path.join(self.d, "docs", "changes.md")
        rc, text = self.finish("--record", record, "--change", "escalate bypass requests",
                               "--requirement", "rule 3")
        self.assertEqual(rc, 4, text)
        self.assertIn("blast radius: 1 of 12 rows", text)
        self.assertIn("better 1 ['r_009'], worse 0", text)
        self.assertIn("VERDICT: NOISE", text)
        with open(record, encoding="utf-8") as fh:
            block = fh.read()
        with open(os.path.join(SKILL, "assets", "change_record.md"), encoding="utf-8") as fh:
            template = re.findall(r"^([A-Z][A-Z ]+):", fh.read(), re.M)
        self.assertEqual(re.findall(r"^([A-Z][A-Z ]+):", block, re.M), template)
        rc, text = run(["--dir", self.exp, "list"])
        self.assertIn("NOISE", text)
        self.assertEqual(self.finish()[0], 2)  # finishing twice is refused

    def test_two_row_gain_ships(self):
        labels = self.labels(["r_009,escalate,none", "r_010,escalate,none", "r_001,assign,S"])
        self.assertEqual(self.start("--labels", labels)[0], 0)
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v2.csv"), self.out)
        with open(self.out, encoding="utf-8") as fh:
            text = fh.read().replace('r_010,assign,M,"size M, 8.0 kg: smallest locker that fits"',
                                     'r_010,escalate,none,"unclear"')
        with open(self.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        rc, text = self.finish()
        self.assertEqual(rc, 0, text)
        self.assertIn("noise floor: UNKNOWN", text)
        self.assertTrue(os.path.isfile(os.path.join(self.exp, "changes.md")))

    def test_blast_radius_counts_rows_that_disappear(self):
        self.assertEqual(self.start("--labels", self.labels(["r_009,escalate,none"]))[0], 0)
        with open(self.out, encoding="utf-8") as fh:
            lines = fh.read().splitlines(True)
        with open(self.out, "w", encoding="utf-8") as fh:
            fh.writelines(lines[:-1])  # the last input row is gone from the output
        rc, text = self.finish()
        self.assertIn("blast radius: 1 of 12 rows", text)

    def test_a_failing_check_rejects(self):
        self.assertEqual(self.start("--labels", self.labels(["r_009,escalate,none"]))[0], 0)
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v0_flawed.csv"), self.out)
        rc, text = self.finish()
        self.assertEqual(rc, 1, text)
        self.assertIn("passed before and fails now", text)

    def test_missing_labels_is_unknown_not_ship(self):
        self.assertEqual(self.start()[0], 0)
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v2.csv"), self.out)
        rc, text = self.finish()
        self.assertEqual(rc, 3, text)
        self.assertIn("UNKNOWN", text)

    def tree(self):
        return {os.path.relpath(os.path.join(dp, f), self.proj): sha(os.path.join(dp, f))
                for dp, _, fs in os.walk(self.proj) for f in fs}

    def test_cmd_is_rerun_and_nothing_outside_its_folders_changes(self):
        src = os.path.join(self.proj, "runs", "output_v2.csv")
        cmd = f'"{PY}" -I -c "import shutil; shutil.copyfile(r\'{src}\', r\'{self.out}\')"'
        before = self.tree()
        shutil.copyfile(os.path.join(self.proj, "runs", "output_v1.csv"), self.out)
        rc, text = run(["--dir", self.exp, "start", "e1", "--output", self.out, "--id-col", "request_id",
                        "--check", self.check, "--labels", self.labels(["r_009,escalate,none"])])
        self.assertEqual(rc, 0, text)  # no --cmd at start: the current output is the baseline
        meta = os.path.join(self.exp, "e1", "meta.json")
        with open(meta, encoding="utf-8") as fh:
            m = fh.read().replace('"cmd": null', '"cmd": ' + __import__("json").dumps(cmd))
        with open(meta, "w", encoding="utf-8") as fh:
            fh.write(m)
        rc, text = self.finish()
        self.assertEqual(rc, 4, text)  # one labeled row better: noise
        after = self.tree()
        changed = sorted(p for p in before if before[p] != after.get(p))
        self.assertEqual(changed, ["output.csv"])  # only the command's own output moved

    def test_usage_errors(self):
        self.assertEqual(run(["--dir", self.exp, "start", "../evil", "--output", self.out,
                              "--id-col", "request_id"])[0], 2)
        self.assertEqual(run(["--dir", self.exp, "start", "e2", "--output", os.path.join(self.d, "none.csv"),
                              "--id-col", "request_id"])[0], 2)
        self.assertEqual(run(["--dir", self.exp, "start", "e3", "--output", self.out, "--id-col", "nope"])[0], 2)
        self.assertEqual(run(["--dir", self.exp, "finish", "never-started"])[0], 2)
        self.assertEqual(run(["--dir", self.exp, "start", "e4", "--output", self.out, "--id-col", "request_id",
                              "--cmd", f'"{PY}" -c "raise SystemExit(5)"'])[0], 2)
        self.assertFalse(os.path.exists(os.path.join(self.exp, "e4")))
        dup = os.path.join(self.d, "dup.csv")
        with open(dup, "w", encoding="utf-8") as fh:
            fh.write("request_id,action\nr_1,a\nr_1,b\n")
        self.assertEqual(run(["--dir", self.exp, "start", "e5", "--output", dup, "--id-col", "request_id"])[0], 2)
        self.assertEqual(self.start()[0], 0)
        self.assertEqual(self.start()[0], 2)  # the name is taken
        self.assertEqual(run(["--dir", os.path.join(self.d, "empty"), "list"])[0], 0)


class HostileExperimentInputs(unittest.TestCase):
    """Hostile-input round 1 (2.4.0): a damaged meta.json (a JSON list, wrong field types,
    nesting deep enough to raise RecursionError) crashed finish and list with a traceback;
    a ragged CSV, a --check that cannot start, and --timeout 0 were accepted and turned
    into a misleading REJECT at finish."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        self.exp = os.path.join(self.d, "exps")
        self.ok = os.path.join(self.d, "ok.csv")
        with open(self.ok, "w", encoding="utf-8") as fh:
            fh.write("id,v\n1,a\n2,b\n")

    def write(self, rel, text):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_damaged_meta_is_a_usage_error(self):
        for i, text in enumerate(["[]", '"x"', '{"status": "started", "cmd": 5}', "[" * 100000]):
            self.write(f"exps/m{i}/meta.json", text)
            rc, out = run(["--dir", self.exp, "finish", f"m{i}"])
            self.assertEqual(rc, 2, out)
            self.assertNotIn("Traceback", out)
        rc, out = run(["--dir", self.exp, "list"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count("damaged meta.json"), 4)

    def test_ragged_csv_is_refused(self):
        bad = self.write("short.csv", "id,v\n1\n2,b,c\n")
        rc, out = run(["--dir", self.exp, "start", "s", "--output", bad, "--id-col", "id"])
        self.assertEqual(rc, 2, out)
        self.assertIn("fields than the header", out)

    def test_record_onto_the_output_or_labels_is_refused(self):
        """Round 3: finish --record output.csv appended the change record to the pipeline's
        own output, which the next run then read as rows."""
        labels = self.write("lab.csv", "id,v\n1,a\n2,a\n")
        for name, target in (("o", self.ok), ("l", labels)):
            with open(target, "rb") as fh:
                before = fh.read()
            self.assertEqual(run(["--dir", self.exp, "start", name, "--output", self.ok, "--id-col", "id",
                                  "--labels", labels])[0], 0)
            rc, out = run(["--dir", self.exp, "finish", name, "--record", target])
            self.assertEqual(rc, 2, out)
            with open(target, "rb") as fh:
                self.assertEqual(fh.read(), before)

    def cmd_experiment(self, name, labels, **extra):
        """start NAME whose --cmd copies cur.csv onto the output, as a real pipeline rewrites it."""
        self.cur = self.write("cur.csv", "id,v\n1,a\n2,b\n3,c\n4,d\n")
        shutil.copyfile(self.cur, self.ok)
        cmd = f'"{PY}" -I -c "import shutil; shutil.copyfile(r\'{self.cur}\', r\'{self.ok}\')"'
        return run(["--dir", self.exp, "start", name, "--output", self.ok, "--id-col", "id", "--cmd", cmd,
                    "--check", f'"{PY}" -c pass', "--labels", labels])

    def test_verifier_labels_equal_to_output_are_refused(self):
        """Independent verifier, B1: --labels pointing at the output (or a link to it) made
        every changed row count as better, so any change shipped."""
        link = os.path.join(self.d, "link.csv")
        os.symlink(self.ok, link)
        for labels in (self.ok, link):
            rc, out = self.cmd_experiment("b1" + str(len(labels)), labels)
            self.assertEqual(rc, 2, out)
            self.assertIn("--labels is the --output file", out)

    def test_verifier_record_cannot_reach_the_output_after_cmd_recreates_it(self):
        """Independent verifier, B2: with the output deleted before finish, the guard saw no
        file, --cmd recreated it, and the record was appended to it; also via a dangling link."""
        labels = self.write("lab.csv", "id,v\n1,a\n2,b\n")
        dangling = os.path.join(self.d, "dang.md")
        os.symlink(self.ok, dangling)
        for name, record in (("b2a", self.ok), ("b2b", dangling)):
            self.assertEqual(self.cmd_experiment(name, labels)[0], 0)
            os.remove(self.ok)
            rc, out = run(["--dir", self.exp, "finish", name, "--record", record])
            self.assertEqual(rc, 2, out)
            self.assertFalse(os.path.exists(self.ok) and "CHANGE:" in open(self.ok, encoding="utf-8").read())

    def test_verifier_planted_symlink_in_the_experiment_folder_is_not_followed(self):
        """Independent verifier, B3: a symlink planted at NAME/after.csv made finish write the
        output over the labels file and then ship on the overwritten labels."""
        labels = self.write("lab2.csv", "id,v\n1,a\n2,b\n3,c\n4,d\n")
        self.assertEqual(self.cmd_experiment("b3", labels)[0], 0)
        os.symlink(labels, os.path.join(self.exp, "b3", "after.csv"))
        with open(self.cur, "w", encoding="utf-8") as fh:
            fh.write("id,v\n1,zz\n2,yy\n3,xx\n4,ww\n")
        rc, out = run(["--dir", self.exp, "finish", "b3"])
        with open(labels, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "id,v\n1,a\n2,b\n3,c\n4,d\n")
        self.assertNotEqual(rc, 0, out)

    def test_verifier_record_inside_an_experiment_folder_and_newline_names(self):
        """Independent verifier, minor: a record inside an experiment folder was lost
        (meta.json) or corrupted another experiment's baseline; a name ending in a newline
        was accepted."""
        labels = self.write("lab.csv", "id,v\n1,a\n2,b\n")
        self.assertEqual(self.cmd_experiment("m1", labels)[0], 0)
        for target in ("m1/meta.json", "m1/baseline.csv"):
            rc, out = run(["--dir", self.exp, "finish", "m1", "--record", os.path.join(self.exp, target)])
            self.assertEqual(rc, 2, out)
        self.assertEqual(run(["--dir", self.exp, "start", "nl\n", "--output", self.ok, "--id-col", "id"])[0], 2)

    def test_check_that_cannot_start_and_zero_timeout_are_refused(self):
        rc, out = run(["--dir", self.exp, "start", "c", "--output", self.ok, "--id-col", "id",
                       "--check", os.path.join(self.d, "no-such-program")])
        self.assertEqual(rc, 2, out)
        self.assertFalse(os.path.exists(os.path.join(self.exp, "c")))
        self.assertEqual(run(["--dir", self.exp, "start", "t", "--output", self.ok, "--id-col", "id",
                              "--timeout", "0"])[0], 2)


if __name__ == "__main__":
    unittest.main()
