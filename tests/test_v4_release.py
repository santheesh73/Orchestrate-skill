"""Fail-closed submission gates and source-grounded interview preparation."""

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import evaluation, interview, records, release
from orchestrate_toolkit.common import ToolkitError, json_bytes


class V4Release(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(ROOT / 'examples/offline', self.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.orchestrate', 'evaluation', '__pycache__'))

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else json_bytes(value))
        return path

    def gate_config(self):
        report = evaluation.evaluate(self.root, 'evaluation.json')
        self.write('final-evaluation.json', report)
        hashes = report['bound_sources']
        self.write('reproduction.json', {'kind': 'reproducibility', 'status': 'PASS', 'reviewer': 'synthetic-test-reviewer',
            'bound_sources': hashes, 'procedure': 'Synthetic supplied record; no live execution is claimed.',
            'commands': [{'argv': ['python', 'main.py'], 'returncode': 0}]})
        self.write('manual.json', {'kind': 'manual_review', 'status': 'PASS', 'reviewer': 'synthetic-test-reviewer',
                                  'requirement': 'semantic-review', 'bound_sources': hashes})
        config = {'contract': 'contract.json', 'evaluation': 'final-evaluation.json',
            'reproducibility': 'reproduction.json', 'dependencies': {'mode': 'standard-library'},
            'required_files': [], 'manual': [{'id': 'semantic-review', 'evidence': 'manual.json'}]}
        self.write('release.json', config)
        return config

    def answers(self):
        self.write('answers.json', {'schema_version': 1, 'answers': [{
            'id': 'answer-1', 'question': 'How is the threshold implemented?',
            'answer': 'This is a synthetic citation test, not an interview transcript.',
            'limitations': 'Free text needs independent review.',
            'evidence': [{'path': 'main.py', 'sha256': records.bound(self.root, ['main.py'])['main.py']}]}]})

    def test_complete_current_supplied_reviews_allow_only_local_ready(self):
        self.gate_config()
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual(report['readiness'], 'READY')
        self.assertEqual(report['official_acceptance'], 'UNKNOWN')
        self.assertEqual(report['blockers'], [])
        self.assertIn('main.py', report['reproducibility_manifest']['source_sha256'])

    def test_missing_manual_and_reproduction_evidence_block(self):
        self.gate_config()
        (self.root / 'manual.json').unlink()
        (self.root / 'reproduction.json').unlink()
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['readiness'], 'BLOCKED')
        self.assertEqual(report['checks']['manual:semantic-review']['status'], 'UNKNOWN')

    def test_stale_final_evaluation_blocks(self):
        self.gate_config()
        self.write('main.py', 'print("new implementation")\n')
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['readiness'], 'BLOCKED')
        self.assertEqual(report['checks']['evaluation']['status'], 'FAIL')

    def test_failed_reproduction_command_cannot_claim_pass(self):
        self.gate_config()
        review = records.load(self.root, 'reproduction.json')
        review['commands'][0]['returncode'] = 1
        self.write('reproduction.json', review)
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['checks']['reproducibility']['status'], 'FAIL')
        self.assertEqual(report['readiness'], 'BLOCKED')

    def test_empty_reproduction_commands_and_partial_bindings_block(self):
        self.gate_config()
        review = records.load(self.root, 'reproduction.json')
        review['commands'] = []
        review['bound_sources'] = records.bound(self.root, ['main.py'])
        self.write('reproduction.json', review)
        self.assertEqual(release.gate(self.root, 'release.json')['readiness'], 'BLOCKED')

    def test_required_transcript_cannot_be_silently_omitted(self):
        config = self.gate_config()
        config['required_files'] = ['log.txt']
        self.write('release.json', config)
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['checks']['required:log.txt']['status'], 'FAIL')
        self.assertEqual(report['readiness'], 'BLOCKED')

    def test_manual_requirement_mismatch_blocks(self):
        self.gate_config()
        review = records.load(self.root, 'manual.json')
        review['requirement'] = 'another-edition'
        self.write('manual.json', review)
        self.assertEqual(release.gate(self.root, 'release.json')['readiness'], 'BLOCKED')

    def test_secrets_are_blocked_without_echoing_match(self):
        token = 'ghp_' + 'A' * 30
        self.write('main.py', 'KEY = "' + token + '"\n')
        self.gate_config()
        report = release.gate(self.root, 'release.json')
        self.assertEqual(report['readiness'], 'BLOCKED')
        self.assertEqual(report['checks']['secrets']['status'], 'FAIL')
        self.assertNotIn(token, str(report))
        self.assertNotIn(token, str(interview.prepare(self.root, ['main.py'])))

    def test_question_bank_contains_difficulty_sources_and_failure_paths(self):
        self.write('main.py', 'LIMIT = 7\ndef run(value):\n    try:\n        return value / LIMIT\n    except TypeError:\n        return None\n')
        report = interview.prepare(self.root, ['main.py'])
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual({q['difficulty'] for q in report['questions']}, {'beginner', 'intermediate', 'advanced'})
        self.assertTrue(all(q['evidence']['sha256'] for q in report['questions']))
        self.assertEqual(report['official_judgment'], 'UNKNOWN')

    def test_constant_claims_detect_incorrect_values_and_missing_names(self):
        self.write('main.py', 'LIMIT = 7\nDYNAMIC = factory()\n')
        self.answers()
        self.write('claims.json', {'claims': [
            {'kind': 'constant', 'path': 'main.py', 'name': 'LIMIT', 'value': 8},
            {'kind': 'constant', 'path': 'main.py', 'name': 'MISSING', 'value': 1},
            {'kind': 'constant', 'path': 'main.py', 'name': 'DYNAMIC', 'value': 1}]})
        report = interview.check(self.root, 'answers.json', 'claims.json')
        self.assertEqual(report['overall'], 'FAIL')
        self.assertEqual(report['checks']['claim_1']['status'], 'FAIL')
        self.assertEqual(report['checks']['claim_2']['status'], 'UNKNOWN')
        self.assertEqual(report['checks']['claim_3']['status'], 'UNKNOWN')

    def test_correct_constant_does_not_verify_free_text(self):
        self.write('main.py', 'LIMIT = 7\n')
        self.answers()
        self.write('claims.json', {'claims': [{'kind': 'constant', 'path': 'main.py', 'name': 'LIMIT', 'value': 7}]})
        report = interview.check(self.root, 'answers.json', 'claims.json')
        self.assertEqual(report['checks']['claim_1']['status'], 'PASS')
        self.assertEqual(report['overall'], 'UNKNOWN')

    def test_invalid_code_is_not_executed(self):
        self.write('main.py', 'this is invalid Python !!!\n')
        report = interview.prepare(self.root, ['main.py'])
        self.assertEqual(report['overall'], 'UNKNOWN')
        self.assertFalse((self.root / 'executed.txt').exists())


if __name__ == '__main__':
    unittest.main()
