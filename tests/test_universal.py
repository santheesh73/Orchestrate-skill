"""Universal adapter/lifecycle, consent, evaluation and checkpoint behavior tests.

These are filesystem and local subprocess simulations, not live agent inference.
"""

import contextlib
import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import adapters, cli, evaluation, execution, installer, workflow
from orchestrate_toolkit.common import ToolkitError, confined, digest, json_bytes, read_json


class Universal(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md'):
            (self.root / name).write_bytes(b'OFFICIAL: preserve exactly\r\n')

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode('utf-8') if isinstance(value, str) else value)
        return path

    def json(self, name, value):
        return self.write(name, json_bytes(value))

    def test_every_adapter_install_doctor_idempotence_and_uninstall(self):
        for agent in adapters.AGENTS:
            with self.subTest(agent=agent):
                first = installer.install(self.root, [agent])
                self.assertEqual(first['status'], 'installed')
                ledger = (self.root / installer.LEDGER).read_bytes()
                result = installer.install(self.root, [agent])
                self.assertEqual(result['status'], 'unchanged')
                self.assertEqual((self.root / installer.LEDGER).read_bytes(), ledger)
                self.assertEqual(installer.doctor(self.root)['installation'], 'PASS')
                installer.uninstall(self.root, [agent])
                self.assertEqual(read_json(self.root / installer.LEDGER)['agents'], [])
                self.assertEqual(read_json(self.root / installer.LEDGER)['files'], {})
                for name in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md'):
                    self.assertEqual((self.root / name).read_bytes(), b'OFFICIAL: preserve exactly\r\n')

    def test_adapter_formats_and_canonical_pointers(self):
        files, owners = adapters.render(list(adapters.AGENTS))
        self.assertIn(b'alwaysApply: false', files['.cursor/rules/orchestrate.mdc'])
        self.assertIn(b'trigger: manual', files['.windsurf/rules/orchestrate.md'])
        self.assertIn(b'applyTo: "**/*"', files['.github/instructions/orchestrate.instructions.md'])
        self.assertIn(b'name:', files['.continue/rules/orchestrate.md'])
        for name, data in files.items():
            self.assertNotIn(name, ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md'))
            if '/adapters/' in name or '/rules/' in name or '/instructions/' in name or '.clinerules/' in name:
                self.assertIn(b'.orchestrate/skills/hackerrank-orchestrate/SKILL.md', data)
        self.assertEqual(owners['.agents/skills/hackerrank-orchestrate/SKILL.md'], ['codex', 'opencode'])
        with mock.patch.object(adapters, 'source_root', return_value=self.root):
            with self.assertRaises(ToolkitError):
                adapters.render(['codex'])

    def test_dry_run_writes_nothing(self):
        before = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*'))
        installer.install(self.root, ['all'], dry_run=True)
        self.assertEqual(sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*')), before)

    def test_unowned_conflict_aborts_before_any_install(self):
        marker = self.write('.cursor/rules/orchestrate.mdc', 'my rule')
        with self.assertRaises(ToolkitError):
            installer.install(self.root, ['all'])
        self.assertEqual(marker.read_text(), 'my rule')
        self.assertFalse((self.root / '.orchestrate').exists())

    def test_shared_files_survive_partial_uninstall(self):
        installer.install(self.root, ['codex', 'opencode', 'cursor'])
        installer.uninstall(self.root, ['codex'])
        self.assertTrue((self.root / '.agents/skills/hackerrank-orchestrate/SKILL.md').exists())
        self.assertEqual(installer.doctor(self.root)['agents'], ['cursor', 'opencode'])
        installer.uninstall(self.root, ['all'])

    def test_user_modified_file_blocks_upgrade_and_uninstall(self):
        installer.install(self.root, ['cursor'])
        rule = self.write('.cursor/rules/orchestrate.mdc', 'user edit')
        with self.assertRaises(ToolkitError):
            installer.install(self.root, ['cursor'], upgrade=True)
        with self.assertRaises(ToolkitError):
            installer.uninstall(self.root, ['cursor'])
        self.assertEqual(rule.read_text(), 'user edit')
        self.assertEqual(installer.doctor(self.root)['installation'], 'FAIL')

    def test_owned_upgrade_creates_backup(self):
        installer.install(self.root, ['cursor'])
        original = adapters.render

        def upgraded(agents, scope='project'):
            files, owners = original(agents, scope)
            files['.cursor/rules/orchestrate.mdc'] += b'\n# new generated version\n'
            return files, owners

        with mock.patch.object(installer, 'render', side_effect=upgraded):
            with self.assertRaises(ToolkitError):
                installer.install(self.root, ['cursor'])
            result = installer.install(self.root, ['cursor'], upgrade=True)
            backup = self.root / result['backup'] / '.cursor/rules/orchestrate.mdc'
            self.assertTrue(backup.exists())
            self.assertNotIn(b'new generated version', backup.read_bytes())

    def test_bad_ledger_cannot_delete_private_files(self):
        installer.install(self.root, ['cursor'])
        path = self.root / installer.LEDGER
        ledger = read_json(path)
        private = self.write('private.txt', 'keep')
        ledger['files']['../private.txt'] = {'sha256': digest(b'keep'), 'owners': ['cursor']}
        path.write_bytes(json_bytes(ledger))
        with self.assertRaises(ToolkitError):
            installer.uninstall(self.root, ['all'])
        self.assertEqual(private.read_text(), 'keep')

    def test_failure_rolls_back_new_install_files(self):
        original = installer.atomic_replace

        def fail_ledger(path, data):
            if path.name == 'install.json':
                raise OSError('simulated disk failure')
            return original(path, data)

        with mock.patch.object(installer, 'atomic_replace', side_effect=fail_ledger):
            with self.assertRaises(OSError):
                installer.install(self.root, ['cursor'])
        self.assertFalse((self.root / '.cursor/rules/orchestrate.mdc').exists())
        self.assertFalse((self.root / installer.LEDGER).exists())

    def test_global_only_uses_documented_native_locations(self):
        for agent in ('codex', 'claude', 'gemini', 'opencode'):
            with self.subTest(agent=agent):
                installer.install(self.root, [agent], scope='user')
                self.assertEqual(installer.doctor(self.root, 'user')['installation'], 'PASS')
                installer.uninstall(self.root, [agent], scope='user')
        with self.assertRaises(ToolkitError):
            installer.install(self.root, ['cursor'], scope='user')

    def test_symlink_install_parent_is_refused(self):
        try:
            os.symlink(self.root / '.orchestrate', self.root / '.cursor', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(ToolkitError):
            installer.install(self.root, ['cursor'])

    def test_runner_requires_consent_and_omits_environment_secrets(self):
        output = self.root / 'executed.txt'
        code = "import os,pathlib; assert 'ORCHESTRATE_PRIVATE_TOKEN' not in os.environ; pathlib.Path('executed.txt').write_text('ok')"
        check = {'name': 'env', 'argv': ['python', '-c', code]}
        with mock.patch.dict(os.environ, {'ORCHESTRATE_PRIVATE_TOKEN': 'secret-do-not-log'}):
            result = execution.run_check(check, self.root)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertFalse(output.exists())
            result = execution.run_check(check, self.root, allow_exec=True)
            self.assertEqual(result['status'], 'PASS')
            self.assertNotIn('secret-do-not-log', json.dumps(result))
            explicit = {'name': 'explicit env', 'argv': ['python', '-c',
                "import os; assert os.environ.get('ORCHESTRATE_PRIVATE_TOKEN') == 'secret-do-not-log'"]}
            result = execution.run_check(explicit, self.root, True, ['ORCHESTRATE_PRIVATE_TOKEN'])
            self.assertEqual(result['status'], 'PASS')
            self.assertNotIn('secret-do-not-log', json.dumps(result))

    def test_runner_bounds_timeout_retries_and_shells(self):
        for check in ({'name': 'bad', 'argv': 'echo hi'},
                      {'name': 'bad', 'argv': ['cmd', '/c', 'echo hi']},
                      {'name': 'bad', 'argv': ['python'], 'retries': 3},
                      {'name': 'bad', 'argv': ['python'], 'timeout': float('nan')}):
            with self.assertRaises(ToolkitError):
                execution.run_check(check, self.root, True)
        result = execution.run_check({'name': 'slow', 'argv': ['python', '-c', 'import time; time.sleep(10)'],
                                      'timeout': 0.05, 'retries': 1}, self.root, True)
        self.assertEqual(result['classification'], 'timeout')
        self.assertEqual(len(result['attempts']), 2)

    def fixture(self):
        self.write('dataset/input.csv', 'id,value\n01,a\n02,b\n')
        self.write('output.csv', 'id,status\n01,ok\n02,review\n')
        self.write('code/main.py', 'print("fixture")\n')
        self.write('problem_statement.md', 'Synthetic contract, not an official score.\n')
        self.json('contract.json', {'input': 'dataset/input.csv', 'output': 'output.csv', 'id_column': 'id',
                                  'columns': ['id', 'status'], 'enums': {'status': ['ok', 'review']},
                                  'require_order': False, 'code_files': ['code/main.py'],
                                  'required_code_files': [], 'artifacts': {'output.csv': 'output.csv'}})
        return self.json('evaluation.json', {'contract': 'contract.json', 'authority': 'problem_statement.md'})

    def test_structured_evaluation_and_regression(self):
        self.fixture()
        report = evaluation.evaluate(self.root, 'evaluation.json')
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual(report['official_score'], 'UNKNOWN')
        self.json('evaluation.json', {'contract': 'contract.json', 'checks': [
            {'name': 'synthetic fixture', 'argv': ['python', '-c', 'raise SystemExit(0)']}]})
        self.assertEqual(evaluation.evaluate(self.root, 'evaluation.json')['overall'], 'UNKNOWN')
        self.assertEqual(evaluation.evaluate(self.root, 'evaluation.json', allow_exec=True)['overall'], 'PASS')
        self.write('baseline.csv', 'id,status\n01,ok\n02,ok\n')
        self.json('evaluation.json', {'contract': 'contract.json', 'baseline': 'baseline.csv', 'replay': 'output.csv'})
        report = evaluation.evaluate(self.root, 'evaluation.json')
        self.assertEqual(report['overall'], 'FAIL')
        self.assertEqual(report['checks']['baseline']['changed_rows'], 1)
        self.assertEqual(report['checks']['replay']['status'], 'PASS')

    def test_usage_prices_and_unknown_evidence(self):
        self.fixture()
        self.write('usage.jsonl', json.dumps({'provider': 'fixture', 'model': 'chosen-at-runtime',
                                            'input_tokens': 100, 'output_tokens': 20, 'run_id': 'final'}) + '\n')
        result = evaluation.usage(self.root, 'usage.jsonl')
        self.assertIsNone(result['estimated_usd'])
        result = evaluation.usage(self.root, 'usage.jsonl', {'chosen-at-runtime': [1, 2]}, 'final')
        self.assertAlmostEqual(result['estimated_usd'], 0.00014)
        self.assertEqual(evaluation.usage(self.root, 'usage.jsonl', run_id='other')['status'], 'UNKNOWN')
        self.write('requirements.txt', 'orchestrate-missing-synthetic-package==0.0\n')
        self.assertEqual(evaluation.requirements(self.root, 'requirements.txt')['status'], 'FAIL')
        self.write('requirements.txt', 'package>=1\n')
        self.assertEqual(evaluation.requirements(self.root, 'requirements.txt')['status'], 'UNKNOWN')
        self.json('evaluation.json', {})
        self.assertEqual(evaluation.evaluate(self.root, 'evaluation.json')['overall'], 'UNKNOWN')

    def test_empty_and_invalid_contract_never_pass(self):
        self.fixture()
        self.write('dataset/input.csv', 'id,value\n')
        self.write('output.csv', 'id,status\n')
        self.assertEqual(evaluation.evaluate(self.root, 'evaluation.json')['overall'], 'UNKNOWN')
        self.write('output.csv', 'id,status\n01,bad\n')
        self.assertEqual(evaluation.evaluate(self.root, 'evaluation.json')['overall'], 'FAIL')

    def test_workflow_resume_gates_stale_reports_and_recovery(self):
        self.fixture()
        workflow.init(self.root)
        self.write('notes.md', 'Reviewed current contract; see code and tests.\n')
        for state in ('ANALYZE', 'PLAN', 'BUILD'):
            workflow.advance(self.root, state, 'notes.md')
        self.assertEqual(workflow.load(self.root)['state'], 'BUILD')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'VALIDATE', 'notes.md')
        report = evaluation.evaluate(self.root, 'evaluation.json')
        self.json('report.json', report)
        workflow.advance(self.root, 'TEST', 'report.json')
        self.write('code/main.py', 'print("changed")\n')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'EVALUATE', 'report.json')
        self.assertEqual(workflow.load(self.root)['state'], 'TEST')
        self.assertEqual(workflow.load(self.root)['failures'], 1)
        workflow.recover(self.root, 'BUILD', 'fix before another test')
        self.assertEqual(workflow.load(self.root)['state'], 'BUILD')

    def test_workflow_full_offline_route_needs_submit_approval(self):
        self.fixture()
        self.write('notes.md', 'Human design and change record evidence.\n')
        workflow.init(self.root)
        report = evaluation.evaluate(self.root, 'evaluation.json')
        self.json('report.json', report)
        for state in workflow.STATES[1:-1]:
            workflow.advance(self.root, state, 'report.json' if state in ('TEST', 'EVALUATE', 'VALIDATE') else 'notes.md')
        pack = evaluation.module('test_package', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
        with contextlib.redirect_stdout(io.StringIO()):
            pack.build(self.root, self.root / 'contract.json', 'submission')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'SUBMIT', 'submission/manifest.json')
        workflow.advance(self.root, 'SUBMIT', 'submission/manifest.json', approve_submit=True)
        self.assertEqual(workflow.load(self.root)['state'], 'SUBMIT')

    def test_starter_mutation_blocks_progress_and_failure_bound(self):
        workflow.init(self.root)
        self.write('AGENTS.md', 'unexpected change')
        self.write('notes.md', 'evidence')
        for _ in range(3):
            with self.assertRaises(ToolkitError):
                workflow.advance(self.root, 'ANALYZE', 'notes.md')
        self.assertEqual(workflow.load(self.root)['failures'], 3)
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'ANALYZE', 'notes.md')

    def test_cli_help_and_evaluation_report_collision(self):
        self.fixture()
        for argv in (['--help'], ['install', '--help'], ['workflow', '--help']):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exc:
                cli.main(argv)
            self.assertEqual(exc.exception.code, 0)
        for argv in (['install', '--agent', 'cursor', '--dry-run'], ['doctor'], ['compatibility'],
                     ['workflow', 'init'], ['workflow', 'status']):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(argv + ['--project', str(self.root)]), 0)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['evaluate', '--project', str(self.root), '--config', 'evaluation.json',
                                       '--report', 'reports/new.json']), 0)
        self.assertEqual(read_json(self.root / 'reports/new.json')['overall'], 'PASS')
        self.write('keep.json', 'private original')
        with contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(['evaluate', '--project', str(self.root), '--config', 'evaluation.json', '--report', 'keep.json'])
        self.assertEqual(rc, 2)
        self.assertEqual((self.root / 'keep.json').read_text(), 'private original')


if __name__ == '__main__':
    unittest.main()
