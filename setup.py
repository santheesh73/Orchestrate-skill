"""Bundle generated copies of canonical skill resources into built distributions."""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithResources(build_py):
    """Keep authored skills in their existing locations; copy only during builds."""

    def run(self):
        super().run()
        root = Path(__file__).parent
        target = Path(self.build_lib) / 'orchestrate_toolkit/resources'
        if target.exists():
            if target.is_symlink() or getattr(target, 'is_junction', lambda: False)():
                raise ValueError('refuse linked build resource directory')
            target.resolve().relative_to(Path(self.build_lib).resolve())
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for name in ('hackerrank-orchestrate', 'skills', 'tools'):
            shutil.copytree(root / name, target / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'VERSION'):
            shutil.copy2(root / name, target / name)


setup(cmdclass={'build_py': BuildWithResources})
