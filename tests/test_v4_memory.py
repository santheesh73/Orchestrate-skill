"""Local score uncertainty, experiment history, mentor evidence and secret redaction."""

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import evaluation, memory, mentor, records, scoring, security
from orchestrate_toolkit.common import ToolkitError, json_bytes


class V4Memory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(ROOT / 'examples/offline', self.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.orchestrate', 'evaluation', '__pycache__'))
        self.write('report.json', evaluation.evaluate(self.root, 'evaluation.json'))

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else json_bytes(value))
        return path

    def score_config(self):
        return {'assumptions': 'Contract shape is a local signal, not semantic correctness.', 'dimensions': [
            {'name': 'shape', 'weight': 0.6, 'criterion_origin': 'local_heuristic',
             'evidence': 'report.json', 'check': 'contract'},
            {'name': 'unmeasured interview', 'weight': 0.4, 'criterion_origin': 'unmeasured'}]}

    def experiment(self):
        self.write('before.json', {'metrics': {'errors': 3, 'latency': 10}, 'failures': [], 'checks': ['PASS']})
        self.write('after.json', {'metrics': {'errors': 1, 'latency': 9}, 'failures': [], 'checks': ['PASS']})
        config = {'id': 'trial-one', 'hypothesis': 'A focused change reduces errors.', 'code_revision': 'supplied-revision',
            'dataset': ['input.csv'], 'sources': ['main.py'], 'configuration': {'strategy': 'fictional'},
            'baseline': 'before.json', 'candidate': 'after.json',
            'directions': {'errors': 'lower', 'latency': 'lower'}, 'reconsideration': 'Repeat on held-apart cases.'}
        self.write('experiment.json', config)
        return config

    def test_missing_score_weight_is_not_renormalized(self):
        self.write('score.json', self.score_config())
        report = scoring.estimate(self.root, 'score.json')
        self.assertIsNone(report['estimate'])
        self.assertEqual(report['known_weight'], 0.6)
        self.assertEqual(report['possible_range'], [60.0, 100.0])
        self.assertEqual(report['official_score'], 'UNKNOWN')

    def test_complete_score_remains_local_and_warns(self):
        config = self.score_config()
        config['dimensions'] = config['dimensions'][:1]
        config['dimensions'][0]['weight'] = 1
        self.write('score.json', config)
        report = scoring.estimate(self.root, 'score.json')
        self.assertEqual(report['estimate'], 100)
        self.assertEqual(report['overall'], 'WARN')
        self.assertEqual(report['basis'], 'LOCAL HEURISTIC ONLY')

    def test_bad_weights_and_unattributed_official_criteria_are_refused(self):
        config = self.score_config()
        config['dimensions'][0]['weight'] = True
        self.write('score.json', config)
        with self.assertRaises(ToolkitError):
            scoring.estimate(self.root, 'score.json')
        config = self.score_config()
        config['dimensions'][0]['criterion_origin'] = 'official_published'
        self.write('score.json', config)
        with self.assertRaises(ToolkitError):
            scoring.estimate(self.root, 'score.json')

    def test_stale_score_evidence_contributes_no_points(self):
        self.write('score.json', self.score_config())
        self.write('main.py', 'changed source\n')
        result = scoring.estimate(self.root, 'score.json')
        self.assertEqual(result['known_weight'], 0)
        self.assertIsNone(result['estimate'])

    def test_experiment_records_real_fingerprints_and_improvements(self):
        config = self.experiment()
        value = memory.create(self.root, 'experiment.json')
        self.assertEqual(value['recommendation'], 'REVIEW')
        self.assertEqual(value['deltas']['errors'], -2)
        self.assertEqual(set(value['improvements']), {'errors', 'latency'})
        self.assertIn('input.csv', value['dataset_sha256'])
        with self.assertRaises(FileExistsError):
            memory.create(self.root, 'experiment.json')
        config['id'] = 'trial-two'
        self.write('experiment-two.json', config)
        memory.create(self.root, 'experiment-two.json')
        compared = memory.compare(self.root, 'trial-one', 'trial-two')
        self.assertTrue(compared['comparable_dataset_and_metric_policy'])
        self.assertEqual(compared['candidate_deltas']['errors'], 0)

    def test_regression_and_new_failure_recommend_rollback(self):
        self.experiment()
        self.write('after.json', {'metrics': {'errors': 5, 'latency': 9}, 'failures': ['broken case'], 'checks': ['FAIL']})
        value = memory.create(self.root, 'experiment.json')
        self.assertEqual(value['recommendation'], 'ROLLBACK_RECOMMENDED')
        self.assertEqual(value['new_failures'], ['broken case'])

    def test_missing_metrics_and_checks_remain_unknown(self):
        self.experiment()
        self.write('after.json', {'metrics': {'errors': 1}, 'failures': [], 'checks': []})
        value = memory.create(self.root, 'experiment.json')
        self.assertEqual(value['recommendation'], 'UNKNOWN')
        self.assertIn('latency', value['missing_metrics'])

    def test_decision_history_is_append_only_and_validates_chain(self):
        self.experiment()
        memory.create(self.root, 'experiment.json')
        for decision in ('DEFER', 'REJECT'):
            self.write('decision.json', {'decision': decision, 'reason': 'Observed evidence needs review.', 'reconsideration': 'New independent evidence.'})
            memory.decide(self.root, 'trial-one', 'decision.json')
        history = memory.history(self.root, 'trial-one')
        self.assertEqual([r['decision'] for r in history['decisions']], ['DEFER', 'REJECT'])
        path = self.root / memory.DIRECTORY / 'trial-one.decisions/0001.json'
        value = records.load(self.root, path.relative_to(self.root).as_posix())
        value['reason'] = 'tampered reason'
        path.write_bytes(json_bytes(value))
        with self.assertRaises(ToolkitError):
            memory.history(self.root, 'trial-one')

    def test_memory_exports_stale_history_without_erasing_it(self):
        self.experiment()
        memory.create(self.root, 'experiment.json')
        self.write('main.py', 'new revision\n')
        report = memory.history(self.root, 'trial-one')
        self.assertEqual(report['current_source_status'], 'FAIL')
        self.assertEqual(len(memory.listing(self.root)['experiments']), 1)

    def test_mentor_references_evidence_and_does_not_predict_gain(self):
        self.write('DESIGN.md', '# Design\nA simple router.\n')
        result = mentor.review(self.root, 'report.json', 'DESIGN.md')
        self.assertEqual(result['overall'], 'UNKNOWN')
        self.assertTrue(result['recommendations'])
        self.assertTrue(all(item['expected_gain'] == 'UNKNOWN' for item in result['recommendations']))
        self.assertTrue(all(item['evidence'] for item in result['recommendations']))

    def test_mentor_missing_evidence_is_honest(self):
        result = mentor.review(self.root)
        self.assertEqual(result['overall'], 'UNKNOWN')
        self.assertIsNone(result['recommendations'][0]['evidence'])

    def test_secret_scan_redacts_matches_and_flags_binary_unknown(self):
        token = 'ghp_' + 'A' * 30
        self.write('secret.txt', 'credential=' + token)
        (self.root / 'binary.bin').write_bytes(b'\xff\x00')
        report = security.scan(self.root, ['secret.txt', 'binary.bin'])
        self.assertEqual(report['overall'], 'FAIL')
        self.assertNotIn(token, str(report))
        self.assertEqual(report['checks']['binary.bin']['status'], 'UNKNOWN')

    def test_credential_metadata_is_not_persisted(self):
        config = self.experiment()
        config['configuration'] = {'secret': 'sk-' + 'A' * 30}
        self.write('experiment.json', config)
        with self.assertRaises(ToolkitError):
            memory.create(self.root, 'experiment.json')
        self.assertFalse((self.root / memory.DIRECTORY / 'trial-one.json').exists())


if __name__ == '__main__':
    unittest.main()
