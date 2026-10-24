"""Companions install without changing the core, and are usable on their own."""

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package_addons


class Companions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.install = self.base / 'installed'
        self.core = self.install / 'hackerrank-orchestrate'
        self.core.mkdir(parents=True)
        (self.core / 'SKILL.md').write_text('existing installed skill\n')

    def run_addons(self, *extra):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            rc = package_addons.main(['--all', '--out', str(self.base / 'dist'),
                                     '--install', str(self.install)] + list(extra))
        return rc, output.getvalue()

    def test_all_companions_install_without_touching_core(self):
        rc, output = self.run_addons()
        self.assertEqual(rc, 0, output)
        self.assertEqual((self.core / 'SKILL.md').read_text(), 'existing installed skill\n')
        for name in package_addons.SKILLS:
            with zipfile.ZipFile(self.base / 'dist' / (name + '.zip')) as archive:
                self.assertIn(name + '/SKILL.md', archive.namelist())
                self.assertIn(name + '/LICENSE', archive.namelist())
                self.assertIn(name + '/THIRD_PARTY_NOTICES.md', archive.namelist())
                self.assertFalse(any('__pycache__' in n for n in archive.namelist()))
        installed = self.install / 'hackerrank-orchestrate-package'
        # Invoke from another directory, in isolated mode, without the repository on sys.path.
        project = self.base / 'project'
        project.mkdir()
        (project / 'input.csv').write_text('id\n1\n', encoding='utf-8')
        (project / 'output.csv').write_text('id,status\n1,ok\n', encoding='utf-8')
        (project / 'main.py').write_text('print("synthetic")\n', encoding='utf-8')
        config = {'input': 'input.csv', 'output': 'output.csv', 'id_column': 'id',
                  'columns': ['id', 'status'], 'require_order': False,
                  'code_files': ['main.py'], 'required_code_files': [],
                  'artifacts': {'output.csv': 'output.csv'}}
        (project / 'contract.json').write_text(json.dumps(config), encoding='utf-8')
        proc = subprocess.run([sys.executable, '-I', '-B',
                               str(installed / 'scripts/package_submission.py'),
                               '--repo', str(project), '--contract', str(project / 'contract.json'),
                               '--out', 'submission'], cwd=str(self.base),
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((project / 'submission/manifest.json').is_file())

    def test_existing_companion_blocks_all_installs(self):
        # Only fixed macOS OS aliases may be normalized; a user-created parent
        # link must still be refused on every platform that permits symlinks.
        linked = self.base / 'linked-install'
        try:
            import os
            os.symlink(self.install, linked, target_is_directory=True)
        except (OSError, NotImplementedError):
            pass
        else:
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                self.assertEqual(package_addons.main(['--all', '--out', str(self.base / 'links'),
                                                       '--install', str(linked)]), 2)
            self.assertFalse((self.base / 'links').exists())
        name = package_addons.SKILLS[-1]
        existing = self.install / name
        existing.mkdir()
        (existing / 'keep.txt').write_text('keep')
        rc, output = self.run_addons()
        self.assertEqual(rc, 2, output)
        self.assertEqual(sorted(p.name for p in self.install.iterdir()), ['hackerrank-orchestrate', name])
        self.assertEqual((existing / 'keep.txt').read_text(), 'keep')
        self.assertFalse((self.base / 'dist').exists())

    def test_existing_archive_is_preserved(self):
        archive = self.base / 'dist' / (package_addons.SKILLS[0] + '.zip')
        archive.parent.mkdir()
        archive.write_bytes(b'previous archive')
        rc, output = self.run_addons()
        self.assertEqual(rc, 2, output)
        self.assertEqual(archive.read_bytes(), b'previous archive')
        self.assertEqual(list(self.install.iterdir()), [self.core])

    def test_partial_copy_rolls_back_only_new_files(self):
        original_stage = package_addons.package_skill.stage

        def fail_install(src, dest):
            if str(dest).startswith(str(self.install)):
                raise OSError('simulated disk failure')
            return original_stage(src, dest)

        with mock.patch.object(package_addons.package_skill, 'stage', side_effect=fail_install):
            rc, output = self.run_addons()
        self.assertEqual(rc, 2, output)
        self.assertEqual(list(self.install.iterdir()), [self.core])
        self.assertFalse(list((self.base / 'dist').glob('*.zip')))

    def test_original_entrypoint_and_checkers_preserved(self):
        manifest = json.loads((ROOT / 'integrations/upstreams.json').read_text())
        for name, expected in manifest['preserved_core_sha256'].items():
            content = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(hashlib.sha256(content).hexdigest(), expected, name)


if __name__ == '__main__':
    unittest.main()
