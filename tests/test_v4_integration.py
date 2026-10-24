"""V4 command dispatch, owned-backup restore and mandatory workflow-policy gates."""

import contextlib
import copy
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import cli, installer, records, workflow
from orchestrate_toolkit.common import ToolkitError, json_bytes


class V4Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write('AGENTS.md', 'OFFICIAL: preserve\n')
        self.write('GEMINI.md', 'OFFICIAL: preserve\n')
        self.write('problem_statement.md', 'Build a router.\nOutput columns id,status.\n')

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else json_bytes(value))
        return path

    def invoke(self, args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            result = cli.main(args + ['--project', str(self.root)])
        return result, out.getvalue()

    def upgrade(self):
        installer.install(self.root, ['cursor'])
        original, owners = installer.render(['cursor'], 'project')
        changed = dict(original)
        name = next(n for n in changed if n.endswith('/SKILL.md'))
        changed[name] += b'\nSynthetic owned upgrade.\n'
        with mock.patch.object(installer, 'render', return_value=(changed, owners)):
            result = installer.install(self.root, ['cursor'], upgrade=True)
        return result['backup'].split('/')[-1], name, original[name]

    def test_v4_commands_have_help(self):
        for name in ('analyze', 'assess', 'estimate', 'mentor', 'interview', 'memory', 'release-gate', 'security', 'restore'):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                cli.main([name, '--help'])
            self.assertEqual(raised.exception.code, 0)

    def test_analysis_cli_returns_unknown_and_readable_report(self):
        code, out = self.invoke(['analyze', '--source', 'problem_statement.md', '--report', 'reports/contract.md', '--format', 'md'])
        self.assertEqual(code, 3)
        self.assertIn('UNKNOWN', out)
        self.assertTrue((self.root / 'reports/contract.md').is_file())
        code, _ = self.invoke(['analyze', '--report', 'reports/contract.md'])
        self.assertEqual(code, 2)

    def test_cli_report_preflight_happens_before_mutation(self):
        self.write('keep.json', 'private user file')
        code, _ = self.invoke(['restore', '--backup', '0' * 32, '--approve-restore', '--report', 'keep.json'])
        self.assertEqual(code, 2)
        self.assertEqual((self.root / 'keep.json').read_text(), 'private user file')
        self.assertFalse((self.root / '.orchestrate').exists())

    def test_restore_preview_and_apply_preserve_official_files(self):
        backup, name, original = self.upgrade()
        before = (self.root / name).read_bytes()
        preview = installer.restore(self.root, backup, dry_run=True)
        self.assertIn(name, preview['files_to_restore'])
        self.assertEqual((self.root / name).read_bytes(), before)
        with self.assertRaises(ToolkitError):
            installer.restore(self.root, backup)
        result = installer.restore(self.root, backup, approve=True)
        self.assertEqual(result['status'], 'restored')
        self.assertEqual((self.root / name).read_bytes(), original)
        self.assertEqual((self.root / 'AGENTS.md').read_bytes(), b'OFFICIAL: preserve\n')
        self.assertEqual(installer.doctor(self.root)['installation'], 'PASS')

    def test_restore_refuses_user_edits_and_tampered_backup(self):
        backup, name, original = self.upgrade()
        self.write(name, 'user edits')
        with self.assertRaises(ToolkitError):
            installer.restore(self.root, backup, approve=True)
        self.assertEqual((self.root / name).read_text(), 'user edits')

    def test_restore_rejects_injected_paths(self):
        with self.assertRaises(ToolkitError):
            installer.restore(self.root, '../outside', dry_run=True)
        backup, name, _ = self.upgrade()
        metadata_name = '.orchestrate/backups/' + backup + '/restore.json'
        value = records.load(self.root, metadata_name)
        value['previous_ledger']['files']['../private'] = {'sha256': '0' * 64, 'owners': ['cursor']}
        self.write(metadata_name, value)
        with self.assertRaises(ToolkitError):
            installer.restore(self.root, backup, approve=True)

    def test_restore_rolls_back_a_caught_write_failure(self):
        backup, name, _ = self.upgrade()
        expected = (self.root / name).read_bytes()
        actual_replace = installer.atomic_replace
        failed = []

        def fail_once(path, data):
            if path == self.root / installer.LEDGER and not failed:
                failed.append(True)
                raise OSError('synthetic interrupted restore')
            return actual_replace(path, data)

        with mock.patch.object(installer, 'atomic_replace', side_effect=fail_once), self.assertRaises(OSError):
            installer.restore(self.root, backup, approve=True)
        self.assertEqual((self.root / name).read_bytes(), expected)
        self.assertEqual(installer.load(self.root, 'project')['history'][-1]['action'], 'install')

    def test_policy_blocks_missing_mandatory_stage_artifact(self):
        self.write('policy.json', {'schema_version': 1, 'required_files': {'ANALYZE': ['contract.json']}, 'release_gate': 'release.json'})
        workflow.init(self.root, 'policy.json')
        self.write('notes.md', 'actual notes')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'ANALYZE', 'notes.md')
        self.assertEqual(workflow.load(self.root)['state'], 'DISCOVER')
        self.write('contract.json', '{}')
        workflow.advance(self.root, 'ANALYZE', 'notes.md')
        self.assertEqual(workflow.load(self.root)['state'], 'ANALYZE')

    def test_policy_mutation_and_gemini_changes_block_progress(self):
        self.write('policy.json', {'schema_version': 1, 'required_files': {}, 'release_gate': 'release.json'})
        workflow.init(self.root, 'policy.json')
        self.write('notes.md', 'notes')
        self.write('GEMINI.md', 'changed official instructions')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'ANALYZE', 'notes.md')
        self.write('GEMINI.md', 'OFFICIAL: preserve\n')
        self.write('policy.json', '{}')
        with self.assertRaises(ToolkitError):
            workflow.advance(self.root, 'ANALYZE', 'notes.md')

    def test_existing_checkpoint_cannot_silently_ignore_a_new_policy(self):
        workflow.init(self.root)
        with self.assertRaises(ToolkitError):
            workflow.init(self.root, 'another-policy.json')

    def test_policy_release_gate_failure_blocks_validation(self):
        self.write('policy.json', {'schema_version': 1, 'required_files': {}, 'release_gate': 'release.json'})
        state = workflow.init(self.root, 'policy.json')
        from orchestrate_toolkit import release
        with mock.patch.object(release, 'gate', return_value={'readiness': 'BLOCKED'}), self.assertRaises(ToolkitError):
            workflow.check_policy(self.root, state, 'VALIDATE')

    def test_complete_synthetic_demo_reaches_local_handoff_without_model_calls(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('v4_demo_test', ROOT / 'tools/v4_demo.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run(self.root / 'demo')
        self.assertEqual(report['overall'], 'PASS')
        self.assertEqual(report['origin'], 'synthetic')
        self.assertEqual(report['live_agent_verification'], 'UNKNOWN')
        self.assertIsNone(report['score']['estimate'])
        self.assertTrue((self.root / 'demo/.orchestrate/submission/code.zip').is_file())


if __name__ == '__main__':
    unittest.main()
