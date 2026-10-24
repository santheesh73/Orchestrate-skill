#!/usr/bin/env python3
"""Offline syntax, metadata and unsafe-subprocess checks for new toolkit sources.

This is targeted static analysis, not a complete security proof or a formatter.
"""

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    errors = []
    paths = (list((ROOT / 'orchestrate_toolkit').glob('*.py')) + list((ROOT / 'tools').glob('*.py'))
             + list((ROOT / 'benchmarks/comparison').glob('*.py')) + [ROOT / 'setup.py'])
    for path in paths:
        source = path.read_text(encoding='utf-8')
        try:
            tree = ast.parse(source, feature_version=(3, 9))
        except SyntaxError as exc:
            errors.append(path.name + ': ' + exc.msg)
            continue
        if not ast.get_docstring(tree):
            errors.append(path.name + ': missing module documentation')
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for key in node.keywords:
                    if key.arg == 'shell' and isinstance(key.value, ast.Constant) and key.value.value is True:
                        errors.append(path.name + ': shell=True is prohibited')
        if any(line.rstrip() != line for line in source.splitlines()):
            errors.append(path.name + ': trailing whitespace')
    for error in errors:
        print('ERROR ' + error)
    print('Static checks: %d files, %d errors' % (len(paths), len(errors)))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
