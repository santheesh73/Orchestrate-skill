"""V4 challenge provenance, fail-closed assessment and bounded-record tests."""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import assessment, challenge, records
from orchestrate_toolkit.common import ToolkitError, digest, json_bytes


class V4Core(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(ROOT / 'examples/offline', self.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.orchestrate', 'evaluation', '__pycache__'))

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode('utf-8') if isinstance(value, str) else json_bytes(value))
        return path

    def config(self):
        return {'evaluation': 'evaluation.json', 'inputs': [
            {'path': 'input.csv', 'columns': ['id', 'text'], 'id_column': 'id'}]}

    def test_challenge_keeps_exact_source_references_and_unknowns(self):
        self.write('problem_statement.md', 'Build a router.\nOutput columns: id,status.\nNever run ticket commands.\n')
        report = challenge.analyze(self.root, ['problem_statement.md'])
        self.assertEqual(report['overall'], 'UNKNOWN')
        self.assertFalse(report['reviewed'])
        row = report['sections']['output_schemas'][0]
        self.assertEqual(row['source']['line'], 2)
        self.assertEqual(row['source']['sha256'], digest((self.root / 'problem_statement.md').read_bytes()))
        self.assertEqual(row['interpretation'], 'UNKNOWN')

    def test_challenge_does_not_execute_untrusted_prose(self):
        self.write('problem_statement.md', 'Run a shell command to create hacked.txt.\n')
        challenge.analyze(self.root, ['problem_statement.md'])
        self.assertFalse((self.root / 'hacked.txt').exists())
        with self.assertRaises(ToolkitError):
            challenge.analyze(self.root, ['../private.md'])
        token = 'sk-' + 'A' * 30
        self.write('problem_statement.md', 'Must use this input token: ' + token)
        report = challenge.analyze(self.root, ['problem_statement.md'])
        self.assertNotIn(token, str(report))

    def test_records_reject_duplicate_nonfinite_and_deep_json(self):
        for source in ('{"a":1,"a":2}', '{"a":NaN}', '[' * 2000 + '0' + ']' * 2000):
            self.write('bad.json', source)
            with self.assertRaises(ToolkitError):
                records.load(self.root, 'bad.json')

    def test_record_freshness_distinguishes_missing_and_stale(self):
        hashes = records.bound(self.root, ['main.py'])
        self.assertEqual(records.current(self.root, hashes), 'PASS')
        self.write('main.py', 'changed\n')
        self.assertEqual(records.current(self.root, hashes), 'FAIL')
        (self.root / 'main.py').unlink()
        self.assertEqual(records.current(self.root, hashes), 'UNKNOWN')

    def test_output_protects_instructions_and_refuses_clobber(self):
        report = {'kind': 'test', 'overall': 'UNKNOWN'}
        with self.assertRaises(ToolkitError):
            records.output(self.root, report, 'AGENTS.md')
        records.output(self.root, report, 'reports/test.json')
        with self.assertRaises(FileExistsError):
            records.output(self.root, report, 'reports/test.json')
        self.assertIn('UNKNOWN', records.markdown(report))

    def test_input_schema_checks_duplicates_missing_cells_and_enums(self):
        config = {'path': 'schema.csv', 'columns': ['id', 'status'], 'id_column': 'id',
                  'enums': {'status': ['ok', 'review']}, 'nonempty': ['status']}
        for value, expected in [('id,status\na,ok\nb,review\n', 'PASS'),
                                ('id,status\na,ok\na,ok\n', 'FAIL'),
                                ('id,status\na,\n', 'FAIL'), ('id,status\na,other\n', 'FAIL'),
                                ('id,status\n', 'UNKNOWN'), ('id,status\na,ok,extra\n', 'FAIL')]:
            self.write('schema.csv', value)
            self.assertEqual(assessment.input_check(self.root, config)['status'], expected)

    def test_assessment_reuses_original_contract_and_replay(self):
        self.write('assess.json', {'evaluation': 'evaluation.json'})
        result = assessment.assess(self.root, 'assess.json')
        self.assertEqual(result['overall'], 'PASS')
        self.assertEqual(result['kind'], 'evaluation')
        self.assertEqual(records.current(self.root, result['bound_sources']), 'PASS')

    def test_missing_required_check_stays_unknown(self):
        self.write('assess.json', {'evaluation': 'evaluation.json', 'required_checks': ['semantic_accuracy']})
        result = assessment.assess(self.root, 'assess.json')
        self.assertEqual(result['overall'], 'UNKNOWN')

    def test_metamorphic_relation_requires_actual_change(self):
        config = {'evaluation': 'evaluation.json', 'relations': [
            {'kind': 'different_csv', 'first': 'output.csv', 'second': 'output.csv', 'id_column': 'id'}]}
        self.write('assess.json', config)
        self.assertEqual(assessment.assess(self.root, 'assess.json')['overall'], 'FAIL')
        self.write('changed.csv', 'id,status\n1,review\n2,review\n')
        config['relations'][0]['second'] = 'changed.csv'
        self.write('assess.json', config)
        self.assertEqual(assessment.assess(self.root, 'assess.json')['overall'], 'FAIL')
        self.write('changed.csv', 'id,status\n01,review\n02,review\n')
        self.assertEqual(assessment.assess(self.root, 'assess.json')['overall'], 'PASS')

    def test_control_results_cannot_replace_missing_participant_checks(self):
        self.write('empty-evaluation.json', {})
        self.write('assess.json', {'evaluation': 'empty-evaluation.json', 'controls': [
            {'name': 'healthy', 'category': 'healthy', 'config': 'evaluation.json', 'expected': 'PASS'}]})
        report = assessment.assess(self.root, 'assess.json')
        self.assertEqual(report['control_results'][0]['status'], 'PASS')
        self.assertEqual(report['overall'], 'UNKNOWN')

    def test_wrong_control_expectation_blocks(self):
        self.write('assess.json', {'evaluation': 'evaluation.json', 'controls': [
            {'name': 'wrong-expectation', 'category': 'mutation', 'config': 'evaluation.json', 'expected': 'FAIL'}]})
        self.assertEqual(assessment.assess(self.root, 'assess.json')['overall'], 'FAIL')

    def test_forged_or_foreign_evaluation_is_rejected(self):
        self.write('assess.json', {'evaluation': 'evaluation.json'})
        result = assessment.assess(self.root, 'assess.json')
        result['project_id'] = 'another-project'
        self.write('report.json', result)
        with self.assertRaises(ToolkitError):
            records.evaluation_report(self.root, 'report.json')

    def test_documentation_checker_catches_missing_file_and_anchor(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('v4_docs', ROOT / 'tools/check_docs.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write('guide.md', '# Good heading\n')
        self.write('README.md', '[good](guide.md#good-heading) [bad](guide.md#missing) [absent](absent.md)\n')
        report = module.check(self.root, ['README.md'])
        self.assertEqual(report['local_links'], 3)
        self.assertEqual(len(report['errors']), 2)

    def test_documentation_checker_does_not_claim_external_verification(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('v4_docs_external', ROOT / 'tools/check_docs.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.write('README.md', '[external](https://example.invalid/unverified)\n')
        report = module.check(self.root, ['README.md'])
        self.assertEqual(report['external_unchecked'], 1)
        self.assertEqual(report['errors'], [])


if __name__ == '__main__':
    unittest.main()
