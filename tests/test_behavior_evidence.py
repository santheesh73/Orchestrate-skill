"""Behavior grader fault controls, paired-trial fairness and stale-evidence regressions."""

import contextlib
import copy
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/hackerrank-orchestrate-evidence/scripts/evidence.py'
SPEC = importlib.util.spec_from_file_location('behavior_evidence', SCRIPT)
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)
SUITE = ROOT / 'evals/behavior'


class BehaviorEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def run_case(self, name='clear-contract', condition='with-skill', trial='1', folder=None):
        return evidence.synthetic_run(SUITE, name, self.base / (folder or name + '-' + condition), condition, trial)

    def report(self, root, name='clear-contract'):
        return evidence.grade(SUITE, name, root)

    def save(self, name, value):
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(evidence.encoded(value))
        return path

    def binding(self, root, name):
        return {'path': name, 'sha256': evidence.sha((root / name).read_bytes()), 'line': 1}

    def requirement(self):
        root = self.base
        for name in ('spec.md', 'main.py', 'output.csv'):
            (root / name).write_text('actual current evidence\n', encoding='utf-8')
        test = {'kind': 'test_result', 'status': 'PASS', 'subject': self.binding(root, 'main.py')}
        self.save('test.json', test)
        value = {'schema_version': 1, 'requirements': [{
            'id': 'R1', 'source': self.binding(root, 'spec.md'),
            'implementation': [self.binding(root, 'main.py')],
            'tests': [self.binding(root, 'test.json')], 'artifacts': [self.binding(root, 'output.csv')]}]}
        self.save('requirements.json', value)
        return value

    def paired(self):
        reports = []
        for condition in ('baseline', 'with-skill'):
            root = self.run_case(condition=condition)
            report = self.report(root)
            reports.append(self.save(condition + '.json', report))
        return reports

    def test_all_healthy_and_injected_controls(self):
        report = evidence.selftest(SUITE)
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual(len(report['checks']), 24)
        self.assertEqual(report['live_verification'], 'UNKNOWN')

    def test_always_pass_grader_is_rejected(self):
        fake = {'overall': 'PASS', 'checks': [{'status': 'PASS', 'detail': 'synthetic broken checker'}]}
        with mock.patch.object(evidence, 'grade', return_value=fake):
            self.assertEqual(evidence.selftest(SUITE)['overall'], 'FAIL')

    def test_always_fail_grader_is_rejected(self):
        fake = {'overall': 'FAIL', 'checks': [{'status': 'FAIL', 'detail': 'synthetic broken checker'}]}
        with mock.patch.object(evidence, 'grade', return_value=fake):
            self.assertEqual(evidence.selftest(SUITE)['overall'], 'FAIL')

    def test_prepare_excludes_expected_answers_and_refuses_reuse(self):
        out = self.base / 'candidate'
        report = evidence.prepare(SUITE, 'clear-contract', out)
        self.assertEqual(report['overall'], 'PASS')
        self.assertFalse((out / 'expected').exists())
        self.assertFalse((out / 'cases').exists())
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['AGENTS.md', 'dataset', 'problem_statement.md'])
        with self.assertRaises(evidence.Invalid):
            evidence.prepare(SUITE, 'clear-contract', out)

    def test_prepare_refuses_traversal_and_linked_destinations(self):
        with self.assertRaises(evidence.Invalid):
            evidence.prepare(SUITE, '../clear-contract', self.base / 'new')
        if sys.platform == 'darwin' and str(self.base).startswith('/private/'):
            alias = Path('/') / self.base.relative_to('/private') / 'os-alias'
            prepared = evidence.prepare(SUITE, 'clear-contract', alias)
            self.assertEqual(prepared['overall'], 'PASS')
        link = self.base / 'link'
        try:
            link.symlink_to(SUITE, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation unavailable')
        with self.assertRaises(evidence.Invalid):
            evidence.prepare(SUITE, 'clear-contract', link / 'candidate')

    def test_missing_output_fails(self):
        root = self.run_case()
        (root / 'output.csv').unlink()
        self.assertEqual(self.report(root)['overall'], 'FAIL')

    def test_wrong_semantics_fails_even_when_schema_is_valid(self):
        root = self.run_case()
        (root / 'output.csv').write_text('id,status\nr1,review\nr2,ok\n', encoding='utf-8')
        self.assertEqual(self.report(root)['overall'], 'FAIL')

    def test_duplicate_header_and_ragged_csv_fail(self):
        root = self.run_case()
        for value in ('id,id\nr1,ok\n', 'id,status\nr1,ok,extra\n', ''):
            (root / 'output.csv').write_text(value, encoding='utf-8')
            self.assertEqual(self.report(root)['overall'], 'FAIL')

    def test_expected_answer_fingerprint_change_rejects_run(self):
        root = self.run_case()
        local = self.base / 'suite'
        shutil.copytree(SUITE, local)
        path = local / 'expected/clear-contract.json'
        path.write_text('{"output": []}', encoding='utf-8')
        with self.assertRaises(evidence.Invalid):
            evidence.grade(local, 'clear-contract', root)

    def test_missing_and_empty_trace_are_unknown(self):
        root = self.run_case()
        (root / 'tool-trace.jsonl').unlink()
        self.assertEqual(next(c for c in self.report(root)['checks'] if c['name'] == 'activation_record')['status'], 'UNKNOWN')
        (root / 'tool-trace.jsonl').write_text('', encoding='utf-8')
        report = self.report(root)
        self.assertEqual(next(c for c in report['checks'] if c['name'] == 'activation_record')['status'], 'UNKNOWN')

    def test_trace_hash_mismatch_and_wrong_activation_fail(self):
        root = self.run_case()
        path = root / 'tool-trace.jsonl'
        event = evidence.loads(path.read_text(encoding='utf-8'))
        event['sha256'] = '0' * 64
        path.write_text(json.dumps(event) + '\n', encoding='utf-8')
        self.assertEqual(self.report(root)['overall'], 'FAIL')
        event = {'event': 'read', **self.binding(root, 'AGENTS.md')}
        del event['line']
        path.write_text(json.dumps(event) + '\n', encoding='utf-8')
        self.assertEqual(self.report(root)['overall'], 'FAIL')

    def test_baseline_skill_loading_is_detected(self):
        root = self.run_case()
        meta = evidence.read(root / 'run.json')
        meta['condition'] = 'baseline'
        (root / 'run.json').write_bytes(evidence.encoded(meta))
        self.assertEqual(self.report(root)['overall'], 'FAIL')

    def test_near_miss_has_no_skill_activation(self):
        root = self.run_case('unrelated-request')
        report = self.report(root, 'unrelated-request')
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual(report['live_verification'], 'UNKNOWN')

    def test_path_escape_and_linked_artifact_are_refused(self):
        root = self.run_case()
        meta = evidence.read(root / 'run.json')
        meta['trace'] = '../private.json'
        (root / 'run.json').write_bytes(evidence.encoded(meta))
        with self.assertRaises(evidence.Invalid):
            self.report(root)
        with self.assertRaises(evidence.Invalid):
            evidence.safe(root, 'C:/private')
        with self.assertRaises(evidence.Invalid):
            evidence.safe(root, 'NUL.json')
        meta['trace'] = 'tool-trace.jsonl'
        (root / 'run.json').write_bytes(evidence.encoded(meta))
        output = root / 'output.csv'
        output.unlink()
        try:
            output.symlink_to(root / 'AGENTS.md')
        except OSError:
            return  # Windows can forbid symlink creation; path tests above still ran.
        with self.assertRaises(evidence.Invalid):
            self.report(root)

    def test_json_duplicates_and_nan_are_refused(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '[' * 2000 + '0' + ']' * 2000):
            with self.assertRaises(evidence.Invalid):
                evidence.loads(value)

    def test_invalid_usage_numbers_are_refused(self):
        root = self.run_case()
        meta = evidence.read(root / 'run.json')
        for value in (-1, True, 'unknown'):
            meta['cost_usd'] = value
            (root / 'run.json').write_bytes(evidence.encoded(meta))
            with self.assertRaises(evidence.Invalid):
                self.report(root)
        del meta['cost_usd']
        meta['schema_version'] = True
        (root / 'run.json').write_bytes(evidence.encoded(meta))
        with self.assertRaises(evidence.Invalid):
            self.report(root)

    def test_paired_comparison_does_not_invent_improvement(self):
        report = evidence.compare(self.paired())
        self.assertEqual(report['overall'], 'UNKNOWN')
        self.assertEqual(len(report['pairs']), 1)
        pair = report['pairs'][0]
        self.assertEqual(pair['baseline_pass'], pair['with_skill_pass'])
        self.assertEqual(pair['improvements'], [])
        self.assertIsNone(pair['usage']['baseline']['cost_usd'])

    def test_unmatched_and_duplicate_runs(self):
        paths = self.paired()
        self.assertEqual(evidence.compare(paths[:1])['unpaired'], [['clear-contract', '1']])
        with self.assertRaises(evidence.Invalid):
            evidence.compare(paths + paths[:1])

    def test_mismatched_model_budget_task_and_grader_are_refused(self):
        paths = self.paired()
        original = evidence.read(paths[1])
        for key in ('model', 'budget', 'agent_version', 'origin', 'task_sha256'):
            value = copy.deepcopy(original)
            value['metadata'][key] = {'calls': 99} if key == 'budget' else 'changed'
            paths[1].write_bytes(evidence.encoded(value))
            with self.assertRaises(evidence.Invalid):
                evidence.compare(paths)
        value = copy.deepcopy(original)
        value['grader_sha256'] = '0' * 64
        paths[1].write_bytes(evidence.encoded(value))
        with self.assertRaises(evidence.Invalid):
            evidence.compare(paths)

    def test_reused_workspace_is_refused(self):
        paths = self.paired()
        left, right = map(evidence.read, paths)
        right['project'] = left['project']
        paths[1].write_bytes(evidence.encoded(right))
        with self.assertRaises(evidence.Invalid):
            evidence.compare(paths)

    def test_comparison_reports_actual_regression_without_activation_gain(self):
        paths = self.paired()
        value = evidence.read(paths[1])
        value['checks'][0]['status'] = 'FAIL'
        value['overall'] = 'FAIL'
        paths[1].write_bytes(evidence.encoded(value))
        report = evidence.compare(paths)
        self.assertEqual(report['pairs'][0]['regressions'], [value['checks'][0]['name']])
        self.assertNotIn('activation_record', report['pairs'][0]['improvements'])

    def test_forged_conclusion_and_changed_denominator_are_refused(self):
        paths = self.paired()
        original = evidence.read(paths[1])
        value = copy.deepcopy(original)
        value['overall'] = 'PASS'
        paths[1].write_bytes(evidence.encoded(value))
        with self.assertRaises(evidence.Invalid):
            evidence.compare(paths)
        value = copy.deepcopy(original)
        value['checks'].append({'name': 'invented', 'status': 'PASS'})
        paths[1].write_bytes(evidence.encoded(value))
        with self.assertRaises(evidence.Invalid):
            evidence.compare(paths)

    def test_complete_requirement_links_still_need_semantic_review(self):
        self.requirement()
        report = evidence.evidence_audit(self.base, 'requirements.json')
        self.assertEqual(report['citation_integrity'], 'PASS')
        self.assertEqual(report['overall'], 'UNKNOWN')

    def test_missing_coverage_is_unknown_and_stale_source_fails(self):
        value = self.requirement()
        value['requirements'][0]['artifacts'] = []
        self.save('requirements.json', value)
        self.assertEqual(evidence.evidence_audit(self.base, 'requirements.json')['citation_integrity'], 'UNKNOWN')
        (self.base / 'spec.md').write_text('changed\n', encoding='utf-8')
        self.assertEqual(evidence.evidence_audit(self.base, 'requirements.json')['overall'], 'FAIL')

    def test_failed_test_and_stale_test_subject_fail(self):
        self.requirement()
        (self.base / 'main.py').write_text('changed implementation\n', encoding='utf-8')
        self.assertEqual(evidence.evidence_audit(self.base, 'requirements.json')['overall'], 'FAIL')
        value = self.requirement()
        test = evidence.read(self.base / 'test.json')
        test['status'] = 'FAIL'
        self.save('test.json', test)
        value['requirements'][0]['tests'] = [self.binding(self.base, 'test.json')]
        self.save('requirements.json', value)
        self.assertEqual(evidence.evidence_audit(self.base, 'requirements.json')['overall'], 'FAIL')

    def test_test_source_alone_is_not_a_test_result(self):
        value = self.requirement()
        value['requirements'][0]['tests'] = [self.binding(self.base, 'main.py')]
        self.save('requirements.json', value)
        with self.assertRaises(ValueError):
            evidence.evidence_audit(self.base, 'requirements.json')

    def test_duplicate_requirement_and_invalid_citation_line_are_refused(self):
        value = self.requirement()
        value['requirements'].append(copy.deepcopy(value['requirements'][0]))
        self.save('requirements.json', value)
        with self.assertRaises(evidence.Invalid):
            evidence.evidence_audit(self.base, 'requirements.json')
        with self.assertRaises(evidence.Invalid):
            evidence.binding(self.base, {**self.binding(self.base, 'main.py'), 'line': True})

    def test_interview_citations_do_not_certify_answer_truth(self):
        (self.base / 'main.py').write_text('print("example")\n', encoding='utf-8')
        value = {'schema_version': 1, 'answers': [{
            'id': 'A1', 'question': 'What does this do?', 'answer': 'An unreviewed answer.',
            'limitations': 'No semantic verification.', 'evidence': [self.binding(self.base, 'main.py')]}]}
        self.save('answers.json', value)
        report = evidence.evidence_audit(self.base, 'answers.json', True)
        self.assertEqual(report['citation_integrity'], 'PASS')
        self.assertEqual(report['overall'], 'UNKNOWN')
        (self.base / 'main.py').write_text('changed\n', encoding='utf-8')
        self.assertEqual(evidence.evidence_audit(self.base, 'answers.json', True)['overall'], 'FAIL')

    def test_empty_evidence_remains_unknown(self):
        self.save('empty.json', {'schema_version': 1, 'requirements': []})
        self.assertEqual(evidence.evidence_audit(self.base, 'empty.json')['overall'], 'UNKNOWN')
        self.assertEqual(evidence.compare([])['overall'], 'UNKNOWN')

    def test_self_contained_installed_script_and_cli_exit_codes(self):
        copied = self.base / 'evidence.py'
        shutil.copy2(SCRIPT, copied)
        proc = subprocess.run([sys.executable, '-I', '-B', str(copied), '--help'],
                              cwd=str(self.base), capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(evidence.main(['grade', '--suite', str(SUITE), '--case', 'invalid',
                                             '--project', str(self.base)]), 2)

    def test_practice_baseline_fails_repair_and_packaging_work(self):
        practice = self.base / 'practice'
        shutil.copytree(ROOT / 'examples/hackathon-practice', practice,
                        ignore=shutil.ignore_patterns('__pycache__', 'output.csv', '.orchestrate'))
        for script in ('baseline.py', 'solution.py'):
            proc = subprocess.run([sys.executable, '-I', '-B', str(practice / script)],
                                  cwd=str(self.base), capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rows = evidence.table(practice / 'output.csv')
            self.assertEqual(len(rows) - 1, 2 if script == 'baseline.py' else 4)
        proc = subprocess.run([sys.executable, '-I', '-B', str(practice / 'record_evidence.py')],
                              capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name, interview in (('requirements', False), ('answers', True)):
            report = evidence.evidence_audit(practice, '.orchestrate/practice-evidence/' + name + '.json', interview)
            self.assertEqual(report['citation_integrity'], 'PASS')
            self.assertEqual(report['overall'], 'UNKNOWN')
        package = ROOT / 'skills/hackerrank-orchestrate-package/scripts/package_submission.py'
        proc = subprocess.run([sys.executable, '-I', '-B', str(package), '--repo', str(practice),
                               '--contract', str(practice / 'submission-contract.json'), '--out', 'submission'],
                              capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((practice / 'submission/manifest.json').is_file())


if __name__ == '__main__':
    unittest.main()
