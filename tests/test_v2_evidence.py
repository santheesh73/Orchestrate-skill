"""Controls for audit sensitivity, benign behavior, unknown coverage and fair metrics."""

import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import audits, cli, evaluation, selftest, workflow
from orchestrate_toolkit.common import ToolkitError, json_bytes

SPEC = importlib.util.spec_from_file_location('comparison_runner', ROOT / 'benchmarks/comparison/run.py')
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


class EvidenceV2(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = copy.deepcopy(selftest.CONTRACT)
        self.data = {k: v.encode('utf-8') for k, v in selftest.FILES.items()}

    def source(self, source):
        self.data['code/main.py'] = source.encode('utf-8')
        return audits.decision_ids(self.config, self.data)

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def test_positive_negative_and_metamorphic_controls(self):
        report = selftest.run()
        self.assertEqual(report['overall'], 'PASS', report)
        self.assertEqual(len(report['controls']), 21)
        for coverage in report['coverage'].values():
            self.assertGreater(coverage['healthy_controls'], 0)
            self.assertGreater(coverage['injected_controls'], 0)
            self.assertEqual(coverage['failed_controls'], 0)
        self.assertEqual(report['kind'], 'audit_selftest')

    def test_selftest_rejects_a_decorative_or_overzealous_checker(self):
        for status in ('PASS', 'FAIL', 'UNKNOWN'):
            with self.subTest(status=status), mock.patch.dict(audits.REGISTRY, {'decision_ids': lambda config, data: {'status': status}}):
                self.assertEqual(selftest.run()['overall'], 'FAIL')
        with mock.patch.object(evaluation, 'contract_check', return_value=({'status': 'PASS'}, None, {})):
            self.assertEqual(selftest.run()['overall'], 'FAIL')
        with mock.patch.object(evaluation, 'compare', return_value={'status': 'PASS'}):
            self.assertEqual(selftest.run()['overall'], 'FAIL')

    def test_decision_ids_use_real_ids_without_executing_source(self):
        for source in ('if row["ticket_id"] == "case_A12": pass\n',
                       'ANSWERS = {"case_B34": "reply"}\n',
                       'result = rows["case_A12"]\n',
                       'if row_id in ("case_A12", "case_B34"): pass\n'):
            with self.subTest(source=source):
                result = self.source(source)
                self.assertEqual(result['status'], 'FAIL')
                self.assertTrue(result['findings'])
                self.assertNotIn('case_A12', json.dumps(result))
        self.assertEqual(self.source('raise RuntimeError("NEVER EXECUTE")\n')['status'], 'PASS')

    def test_benign_comments_docstrings_assignments_and_unseen_ids(self):
        for source in ('# case_A12\nx = 1\n', '"""case_A12"""\nx = 1\n',
                       'probe_id = "case_A12"\n', 'if row_id == "case_Z99": pass\n'):
            with self.subTest(source=source):
                self.assertEqual(self.source(source)['status'], 'PASS')

    def test_empty_unsupported_and_invalid_source_are_unknown(self):
        self.assertEqual(self.source('def (broken syntax')['status'], 'UNKNOWN')
        for name in ('code/main.ts', 'code/main.cpp', 'code/runner'):
            self.config['code_files'] = ['code/main.py', name]
            self.data['code/main.py'] = b'def decide(text): return "reply"\n'
            self.data[name] = b'unsupported language'
            self.assertEqual(audits.decision_ids(self.config, self.data)['status'], 'UNKNOWN')
        self.config['code_files'] = ['usage.md']
        self.assertEqual(audits.decision_ids(self.config, self.data)['status'], 'UNKNOWN')

    def test_closed_registry_and_missing_contract_cannot_silently_pass(self):
        for names in ('decision_ids', ['unknown'], ['decision_ids', 'decision_ids'], [['decision_ids']]):
            with self.subTest(names=names), self.assertRaises(ToolkitError):
                audits.run(names, self.config, self.data)
        self.assertEqual(audits.run(['decision_ids'], None, {})['decision_ids']['status'], 'UNKNOWN')

    def test_evaluation_plugin_is_opt_in_and_preserves_source_bindings(self):
        self.source('if row_id == "case_A12": pass\n')
        for name, raw in self.data.items():
            self.write(name, raw)
        self.write('contract.json', json_bytes(self.config))
        self.write('eval.json', json_bytes({'contract': 'contract.json'}))
        baseline = evaluation.evaluate(self.root, 'eval.json')
        self.assertEqual(baseline['overall'], 'PASS')
        self.write('eval.json', json_bytes({'contract': 'contract.json', 'contract_audits': ['decision_ids']}))
        result = evaluation.evaluate(self.root, 'eval.json')
        self.assertEqual(result['overall'], 'FAIL')
        self.assertEqual(result['checks']['audit_decision_ids']['status'], 'FAIL')
        self.assertIn('code/main.py', result['bound_sources'])
        self.assertFalse(result['execution_authorized'])

    def test_unknown_status_and_selftest_cannot_be_submission_evidence(self):
        self.assertEqual(evaluation.worst(['PASS', 'WARN']), 'WARN')
        self.assertEqual(evaluation.worst(['WARN', 'UNKNOWN']), 'UNKNOWN')
        self.assertEqual(evaluation.worst(['UNKNOWN', 'FAIL']), 'FAIL')
        self.write('AGENTS.md', b'OFFICIAL RULES\n')
        self.write('notes.md', b'plan\n')
        workflow.init(self.root)
        for state in ('ANALYZE', 'PLAN', 'BUILD'):
            workflow.advance(self.root, state, 'notes.md')
        self.write('report.json', json_bytes(selftest.run()))
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'TEST', 'report.json')

    def test_cli_selftest_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(cli.main(['audit-selftest']), 0)
        self.assertEqual(json.loads(stream.getvalue())['kind'], 'audit_selftest')
        with mock.patch.object(selftest, 'run', return_value={'overall': 'FAIL'}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['audit-selftest']), 1)

    def test_comparison_unknowns_are_excluded_from_accuracy_denominators(self):
        rows = [{'defect': False, 'actual': 'PASS', 'seconds': 1},
                {'defect': False, 'actual': 'FAIL', 'seconds': 2},
                {'defect': True, 'actual': 'UNKNOWN', 'seconds': 3},
                {'defect': True, 'actual': 'PASS', 'seconds': 4}]
        report = comparison.rates(rows)
        self.assertEqual(report['false_positive_rate'], 0.5)
        self.assertEqual(report['false_negative_rate'], 1)
        self.assertEqual(report['unknown'], 1)
        self.assertIsNone(comparison.rates([])['false_negative_rate'])
        rows.append({'defect': True, 'actual': 'PASS', 'seconds': 1, 'policy_support': 'N/A'})
        self.assertEqual(comparison.rates(rows)['defective_executed'], 1)
        self.assertEqual(comparison.rates(rows)['not_applicable'], 1)

    def test_identical_fixtures_and_expected_packaging_controls(self):
        suite = comparison.fixtures()
        names = [case['id'] for case in suite['cases']]
        self.assertEqual(len(names), len(set(names)))
        for case in suite['cases']:
            with self.subTest(case=case['id']):
                result = comparison.run_case(ROOT, 'own', suite, case, 'decision_ids')
                self.assertEqual(result['actual'], result['expected'], result)
                with tempfile.TemporaryDirectory() as other:
                    root = Path(other).resolve()
                    hashes = comparison.materialize(root, suite, case)
                    self.assertEqual(result['input_sha256'], hashes)
                    if case['category'] == 'leakage':
                        self.assertEqual(evaluation.contract_check(root, 'contract.json')[0]['status'], 'PASS')
                        (root / 'evaluation.json').write_bytes(json_bytes(
                            {'contract': 'contract.json', 'contract_audits': ['decision_ids']}))
                        self.assertEqual(evaluation.evaluate(root, 'evaluation.json')['overall'], result['expected'])

    def test_unexecuted_competitor_is_unknown_not_pass(self):
        with mock.patch.object(comparison, 'fixtures', return_value={'cases': []}), \
                mock.patch.object(comparison, 'installation', return_value={'conflict_preservation': 'UNKNOWN'}):
            report = comparison.compare(ROOT, ROOT, allow_competitor=False)
        self.assertEqual(report['engines']['competitor']['status'], 'UNKNOWN')
        self.assertEqual(report['overall_superiority'], 'UNKNOWN')
        with mock.patch.object(comparison, 'process', return_value=({'returncode': 2}, b'installer error')):
            result = comparison.installation(ROOT, 'own')
        self.assertEqual(result['conflict_preservation'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
