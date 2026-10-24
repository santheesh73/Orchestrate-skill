"""Behavioral and negative-control checks for contract-driven submission bundles."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/hackerrank-orchestrate-package/scripts/package_submission.py'
SPEC = importlib.util.spec_from_file_location('submission_package', SCRIPT)
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class SubmissionPackage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.write('dataset/inputs.csv', 'id,value\n01,one\n02,two\n')
        self.write('output.csv', 'id,status,reason\n01,ok,source one\n02,review,missing evidence\n')
        self.write('code/main.py', 'print("fixture")\n')
        self.write('README.md', 'Run code/main.py\n')
        self.write('evaluation/usage_report.md', 'Final run: no model calls.\n')
        self.write('log.txt', 'Synthetic test transcript\n')
        self.config = {
            'input': 'dataset/inputs.csv', 'output': 'output.csv', 'id_column': 'id',
            'columns': ['id', 'status', 'reason'], 'enums': {'status': ['ok', 'review']},
            'allow_blank': [], 'require_order': False,
            'code_files': ['code/main.py', 'README.md', 'evaluation/usage_report.md'],
            'required_code_files': ['evaluation/usage_report.md'],
            'artifacts': {'output.csv': 'output.csv', 'log.txt': 'log.txt'}, 'hashes': {}}

    def write(self, name, data):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
        return target

    def run_package(self, config=None, out='submission', extra=()):
        config = self.config if config is None else config
        path = self.write('contract.json', json.dumps(config))
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = package.main(['--repo', str(self.repo), '--contract', str(path),
                                   '--out', out] + list(extra))
        return result, stream.getvalue()

    def assert_failure(self, expected=None):
        rc, output = self.run_package()
        if expected is None:
            self.assertNotEqual(rc, 0, output)
        else:
            self.assertEqual(rc, expected, output)
        self.assertNotIn('PACKAGE BUILT', output)
        self.assertFalse((self.repo / 'submission').exists())
        self.assertFalse(list(self.repo.glob('.submission-*')))

    def test_build_contains_exact_allowlist_and_verifiable_hashes(self):
        self.write('unlisted.txt', 'must stay outside archive')
        rc, output = self.run_package()
        self.assertEqual(rc, 0, output)
        bundle = self.repo / 'submission'
        with zipfile.ZipFile(bundle / 'code.zip') as archive:
            self.assertEqual(set(archive.namelist()), set(self.config['code_files']))
            self.assertEqual(archive.read('code/main.py'), (self.repo / 'code/main.py').read_bytes())
        manifest = json.loads((bundle / 'manifest.json').read_text())
        for name, digest in manifest['bundle_sha256'].items():
            self.assertEqual(hashlib.sha256((bundle / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(manifest['rows'], 2)
        self.assertEqual(manifest['source_sha256']['output.csv'],
                         hashlib.sha256((bundle / 'output.csv').read_bytes()).hexdigest())
        self.assertEqual(set(manifest['archive_members']), set(self.config['code_files']))

    def test_empty_csv_is_unknown_and_never_published(self):
        self.write('dataset/inputs.csv', 'id,value\n')
        self.write('output.csv', 'id,status,reason\n')
        self.assert_failure(3)

    def test_missing_required_usage_file_never_reports_success(self):
        (self.repo / 'evaluation/usage_report.md').unlink()
        self.assert_failure(2)

    def test_required_file_omitted_from_archive_allowlist(self):
        self.config['code_files'].remove('evaluation/usage_report.md')
        self.assert_failure(1)

    def test_check_only_leaves_sources_and_destination_unchanged(self):
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes()
                  for p in self.repo.rglob('*') if p.is_file()}
        rc, output = self.run_package(extra=['--check-only'])
        self.assertEqual(rc, 0, output)
        self.assertFalse((self.repo / 'submission').exists())
        for name, content in before.items():
            self.assertEqual((self.repo / name).read_bytes(), content)

    def test_existing_destination_is_preserved(self):
        marker = self.write('submission/keep.txt', 'previous package')
        rc, output = self.run_package()
        self.assertEqual(rc, 2, output)
        self.assertEqual(marker.read_text(), 'previous package')
        self.assertEqual(list(marker.parent.iterdir()), [marker])

    def test_non_root_output_and_optional_order(self):
        self.config['output'] = 'runs/result.csv'
        self.config['artifacts']['final.csv'] = self.config['artifacts'].pop('output.csv')
        self.config['artifacts']['final.csv'] = 'runs/result.csv'
        self.write('runs/result.csv', 'id,status,reason\n02,review,two\n01,ok,one\n')
        rc, output = self.run_package(out='bundle-one')
        self.assertEqual(rc, 0, output)
        self.config['require_order'] = True
        rc, output = self.run_package(out='bundle-two')
        self.assertEqual(rc, 1, output)
        self.assertFalse((self.repo / 'bundle-two').exists())

    def test_csv_shape_and_enum_negative_controls(self):
        cases = [
            'id,status,status\n01,ok,one\n02,review,two\n',
            'status,id,reason\nok,01,one\nreview,02,two\n',
            'id,status,reason\n01,ok,one\n01,review,two\n',
            'id,status,reason\n01,ok,one\n',
            'id,status,reason\n01,ok,one\n03,review,two\n',
            'id,status,reason\n01,invalid,one\n02,review,two\n',
            'id,status,reason\n01,ok,\n02,review,two\n',
            'id,status,reason\n01,ok,one,extra\n02,review,two\n',
            'id,status,reason\n01,ok\n02,review,two\n',
            'id,status,reason\n01,ok,"unclosed\n02,review,two\n',
            b'id,status,reason\n01,ok,\xff\n02,review,two\n',
            'id,status,reason\n01,ok,\x00\n02,review,two\n']
        for content in cases:
            with self.subTest(content=repr(content)):
                self.write('output.csv', content)
                self.assert_failure()

    def test_duplicate_input_ids_are_rejected(self):
        self.write('dataset/inputs.csv', 'id,value\n01,one\n01,two\n')
        self.assert_failure(1)

    def test_blank_field_allowed_only_when_explicit(self):
        self.write('output.csv', 'id,status,reason\n01,ok,\n02,review,two\n')
        self.config['allow_blank'] = ['reason']
        rc, output = self.run_package()
        self.assertEqual(rc, 0, output)

    def test_pinned_hash_detects_stale_final_run(self):
        self.config['hashes']['output.csv'] = '0' * 64
        self.assert_failure(1)
        self.config['hashes']['output.csv'] = hashlib.sha256((self.repo / 'output.csv').read_bytes()).hexdigest()
        rc, output = self.run_package()
        self.assertEqual(rc, 0, output)

    def test_malformed_contracts_and_collisions(self):
        bad = []
        for key, value in [('require_order', 'false'), ('columns', 'id,status'),
                           ('enums', {'status': 'ok'}), ('hashes', {'output.csv': 'bad'}),
                           ('allow_blank', ['id']), ('code_files', []),
                           ('id_column', None), ('new_typo', True)]:
            cfg = copy.deepcopy(self.config)
            cfg[key] = value
            bad.append(cfg)
        for artifacts in [{'code.zip': 'output.csv'}, {'a': 'output.csv', 'a/b': 'log.txt'},
                          {'out.csv': 'output.csv', 'OUT.CSV': 'log.txt'},
                          {'../output.csv': 'output.csv'}]:
            cfg = copy.deepcopy(self.config)
            cfg['artifacts'] = artifacts
            bad.append(cfg)
        for cfg in bad:
            with self.subTest(cfg=cfg):
                rc, output = self.run_package(cfg)
                self.assertEqual(rc, 2, output)
                self.assertFalse((self.repo / 'submission').exists())

    def test_path_traversal_environment_dataset_and_keys_refused(self):
        for name in ['../elsewhere.py', '/tmp/code.py', 'C:/code.py', '.env.local',
                     '.aws/credentials', 'private.key', 'dataset/inputs.csv',
                     '.agents/skills/x.py', 'code/NUL.py', 'code//main.py']:
            with self.subTest(name=name):
                cfg = copy.deepcopy(self.config)
                cfg['code_files'].append(name)
                rc, output = self.run_package(cfg)
                self.assertEqual(rc, 2, output)

    def test_secret_in_selected_text_detected_without_disclosure(self):
        secret = 'sk-' + 'a' * 24
        self.write('code/main.py', 'KEY = "' + secret + '"\n')
        rc, output = self.run_package()
        self.assertEqual(rc, 1, output)
        self.assertNotIn(secret, output)
        self.assertFalse((self.repo / 'submission').exists())

    def test_symlink_source_and_destination_refused(self):
        try:
            os.symlink(self.repo / 'README.md', self.repo / 'linked.md')
            os.symlink(self.repo / 'evaluation', self.repo / 'out-link', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlink creation unavailable')
        self.config['code_files'].append('linked.md')
        self.assert_failure(2)
        self.config['code_files'].remove('linked.md')
        rc, output = self.run_package(out='out-link/new')
        self.assertEqual(rc, 2, output)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX named pipes only')
    def test_fifo_is_rejected_without_opening(self):
        os.mkfifo(self.repo / 'pipe.py')
        self.config['code_files'].append('pipe.py')
        self.assert_failure(2)

    def test_build_failure_publishes_nothing_and_keeps_sources(self):
        before = (self.repo / 'output.csv').read_bytes()
        with mock.patch.object(package.os, 'rename', side_effect=OSError('simulated failure')):
            self.assert_failure(2)
        self.assertEqual((self.repo / 'output.csv').read_bytes(), before)

    def test_identical_snapshot_produces_identical_archive(self):
        self.assertEqual(self.run_package(out='first')[0], 0)
        self.assertEqual(self.run_package(out='second')[0], 0)
        self.assertEqual((self.repo / 'first/code.zip').read_bytes(),
                         (self.repo / 'second/code.zip').read_bytes())

    def test_second_edition_schema_has_no_usage_or_readme_assumption(self):
        self.write('facts.csv', 'item_id,text\nx,hello\n')
        self.write('results/answers.csv', 'item_id,label\nx,route\n')
        config = {'input': 'facts.csv', 'output': 'results/answers.csv', 'id_column': 'item_id',
                  'columns': ['item_id', 'label'], 'enums': {'label': ['route']},
                  'require_order': True, 'code_files': ['code/main.py'],
                  'required_code_files': [], 'artifacts': {'answers.csv': 'results/answers.csv'}}
        rc, output = self.run_package(config)
        self.assertEqual(rc, 0, output)
        with zipfile.ZipFile(self.repo / 'submission/code.zip') as archive:
            self.assertEqual(archive.namelist(), ['code/main.py'])


if __name__ == '__main__':
    unittest.main()
