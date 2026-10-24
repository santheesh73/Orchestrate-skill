"""Isolated adapters for trusted pinned checkers; fixture code is never executed."""

import argparse
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path


def load(path):
    spec = importlib.util.spec_from_file_location('benchmark_checker', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--engine', choices=['own', 'competitor'], required=True)
    parser.add_argument('--audit', choices=['corpus_literals', 'decision_ids'], default='corpus_literals')
    args = parser.parse_args()
    root = args.fixture.resolve()
    with contextlib.redirect_stdout(io.StringIO()):
        if args.engine == 'own':
            if args.audit == 'decision_ids':
                sys.path.insert(0, str(args.repo))
                from orchestrate_toolkit.audits import decision_ids
                config = json.loads((root / 'contract.json').read_text(encoding='utf-8'))
                data = {name: (root / name).read_bytes() for name in [config['input']] + config['code_files']}
                status = decision_ids(config, data)['status']
            else:
                module = load(args.repo / 'hackerrank-orchestrate/scripts/corpus_literals.py')
                stats = {}
                findings = module.scan([str(root / 'dataset/inputs.csv')], [str(root / 'code')], stats=stats)
                status = ('UNKNOWN' if not stats['files'] or not stats['values'] else
                          'FAIL' if findings else 'PASS')
        else:
            sys.path.insert(0, str(args.repo))
            from orchestrate_kit.evaluator.plugin_api import RepoContext
            from orchestrate_kit.evaluator.plugins.orchestrate.leakage import audit_label_leakage
            result = audit_label_leakage(RepoContext(root=root))
            status = 'UNKNOWN' if result.skipped else 'PASS' if result.passed else 'FAIL'
    print(json.dumps({'status': status}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
