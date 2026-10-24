#!/usr/bin/env python3
"""Validate, package and optionally install the additive companion skills.

Failure it prevents: an optional installation replacing the existing core skill or
silently overwriting another companion. Existing destinations are always refused.
The original package_skill.py command and archive format are unchanged.
Exit 0 success, 1 invalid skill, 2 usage/path/collision/I/O error.
"""

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_skill
import validate_skill

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('hackerrank-orchestrate-design', 'hackerrank-orchestrate-package',
          'hackerrank-orchestrate-practice', 'hackerrank-orchestrate-toolkit')


def installation_path(value):
    """Normalize macOS's fixed OS aliases, while refusing user-created links below them."""
    path = value.expanduser().absolute()
    if sys.platform == 'darwin':
        for name in ('var', 'tmp', 'etc'):
            alias, actual = Path('/') / name, Path('/private') / name
            if (path == alias or alias in path.parents) and alias.is_symlink() and alias.resolve() == actual:
                path = actual / path.relative_to(alias)
                break
    return path


def validate(root=ROOT):
    errors = []
    for name in SKILLS:
        validate_skill.check_skill(str(root / 'skills' / name), errors)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', choices=SKILLS, action='append', default=[])
    parser.add_argument('--all', action='store_true', help='select all companions, never the core skill')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    parser.add_argument('--install', type=Path, help='skill directory; existing folders are never replaced')
    args = parser.parse_args(argv)
    selected = list(SKILLS) if args.all or args.validate_only else sorted(set(args.skill))
    if not selected:
        parser.error('select --all or at least one --skill')
    try:
        errors = []
        for name in selected:
            validate_skill.check_skill(str(ROOT / 'skills' / name), errors)
        if errors:
            for error in errors:
                print('ERROR ' + error)
            return 1
        if args.validate_only:
            print('Validated %d companion skills; core unchanged' % len(selected))
            return 0
        out = args.out.expanduser().resolve()
        install = installation_path(args.install) if args.install else None
        # Avoid following a user-selected installation link or polluting source folders.
        if install and any(p.is_symlink() for p in [install] + list(install.parents)):
            raise ValueError('install path contains a symlink')
        for place in [out] + ([install.resolve()] if install else []):
            if place == ROOT or place in ROOT.parents or ROOT / 'skills' == place or ROOT / 'skills' in place.parents:
                raise ValueError('destination overlaps repository sources')
            if ROOT / 'hackerrank-orchestrate' == place or ROOT / 'hackerrank-orchestrate' in place.parents:
                raise ValueError('destination overlaps the original skill')
        for name in selected:
            if os.path.lexists(out / (name + '.zip')):
                raise ValueError('archive already exists: ' + name)
            if install and os.path.lexists(install / name):
                raise ValueError('skill already exists; nothing replaced: ' + name)
        if out.exists() and not out.is_dir() or install and install.exists() and not install.is_dir():
            raise ValueError('destination is not a directory')
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for name in selected:
                staged = temp / name
                package_skill.stage(str(ROOT / 'skills' / name), str(staged))
                shutil.copy2(ROOT / 'LICENSE', staged / 'LICENSE')
                shutil.copy2(ROOT / 'THIRD_PARTY_NOTICES.md', staged / 'THIRD_PARTY_NOTICES.md')
                errors = []
                validate_skill.check_skill(str(staged), errors)
                if errors:
                    raise ValueError('staged skill failed validation: ' + errors[0])
                with zipfile.ZipFile(temp / (name + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
                    for path, rel in package_skill.skill_files(str(staged)):
                        archive.write(path, name + '/' + rel.replace(os.sep, '/'))
            # Preflight all destinations before the first install; roll back new items
            # on failure. Existing folders and the core skill are never moved/deleted.
            created = []
            try:
                out.mkdir(parents=True, exist_ok=True)
                if install:
                    install.mkdir(parents=True, exist_ok=True)
                for name in selected:
                    archive_path = out / (name + '.zip')
                    with archive_path.open('xb') as target:
                        created.append(archive_path)
                        target.write((temp / (name + '.zip')).read_bytes())
                    if install:
                        target = install / name
                        # mkdir is the no-clobber reservation; don't follow a link or
                        # delete a concurrent install if reservation fails.
                        target.mkdir()
                        created.append(target)
                        package_skill.stage(str(temp / name), str(target))
                        errors = []
                        validate_skill.check_skill(str(target), errors)
                        if errors:
                            raise ValueError('installed skill failed validation: ' + errors[0])
                    print('Packaged ' + name + (' and installed' if install else ''))
            except (OSError, ValueError):
                for path in reversed(created):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                raise
        return 0
    except (OSError, ValueError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='backslashreplace')
    sys.exit(main())
