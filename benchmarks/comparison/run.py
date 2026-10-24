"""Compare trusted checkers on identical synthetic artifacts; never run fixture code.

The competitor checkout is optional. Executing its reviewed scripts requires
--allow-competitor-exec. Missing capabilities remain UNKNOWN or N/A, never PASS.
JSON reports are new files only. This is a synthetic diagnostic, not a ranking.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OWN_PACKAGE = 'skills/hackerrank-orchestrate-package/scripts/package_submission.py'
OTHER_PACKAGE = 'skills/orchestrate-package/scripts/package_submission.py'
LIMIT = 32 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixtures():
    value = json.loads((HERE / 'fixtures.json').read_text(encoding='utf-8'))
    names = set()
    for case in value['cases']:
        if case['id'] in names or type(case['defect']) is not bool:
            raise ValueError('invalid or duplicate fixture identity')
        names.add(case['id'])
        for name in list(value['files']) + list(case['overlay']):
            parts = name.split('/')
            if any(p in ('', '.', '..') for p in parts) or '\\' in name or ':' in name:
                raise ValueError('unsafe fixture path')
    return value


def materialize(root, suite, case):
    files = dict(suite['files'], **case['overlay'])
    hashes = {}
    for name, content in files.items():
        if content is None:
            continue
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = content.encode('utf-8')
        path.write_bytes(raw)
        hashes[name] = sha(raw)
    # Adapter metadata is identical for both runs. It is not a fixture mutation.
    code = ['code/main.py', 'README.md', 'evaluation/usage_report.md']
    code += sorted(n for n in files if n.startswith('code/') and n not in code and files[n] is not None)
    contract = {'input': 'dataset/inputs.csv', 'output': 'output.csv', 'id_column': 'message_id',
                'columns': ['message_id', 'action', 'reason'], 'require_order': True,
                'enums': {'action': ['notify', 'digest']}, 'code_files': code,
                'required_code_files': ['evaluation/usage_report.md'],
                'artifacts': {'output.csv': 'output.csv', 'log.txt': 'log.txt'}}
    raw = json.dumps(contract).encode('utf-8')
    (root / 'contract.json').write_bytes(raw)
    hashes['contract.json'] = sha(raw)
    return hashes


def process(argv, cwd, timeout=30, home=None):
    env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if k in os.environ}
    if home is not None:
        env['HOME'] = str(home)
        env['USERPROFILE'] = str(home)
    start = time.perf_counter()
    try:
        with tempfile.TemporaryFile() as output:
            proc = subprocess.run(argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                                  stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
            output.seek(0)
            raw = output.read(LIMIT + 1)
        return {'returncode': proc.returncode, 'seconds': time.perf_counter() - start,
                'output_sha256': sha(raw), 'crashed': b'Traceback (most recent call last)' in raw,
                'oversized': len(raw) > LIMIT}, raw
    except (OSError, subprocess.TimeoutExpired):
        return {'returncode': None, 'seconds': time.perf_counter() - start,
                'status': 'UNKNOWN', 'reason': 'process_unavailable_or_timeout'}, b''


def revision(repo, sources):
    evidence, raw = process(['git', 'rev-parse', 'HEAD'], repo)
    rev = raw.decode('ascii', errors='replace').strip() if evidence['returncode'] == 0 else 'UNKNOWN'
    _, dirty = process(['git', 'status', '--porcelain'], repo)
    return {'revision': rev, 'working_tree_dirty': bool(dirty),
            'checker_sha256': {n: sha((repo / n).read_bytes()) for n in sources if (repo / n).is_file()}}


def run_case(repo, engine, suite, case, own_audit='corpus_literals'):
    with tempfile.TemporaryDirectory(prefix='orchestrate-comparison-') as temp:
        root = Path(temp).resolve()
        hashes = materialize(root, suite, case)
        if case['category'] == 'packaging':
            script = repo / (OWN_PACKAGE if engine == 'own' else OTHER_PACKAGE)
            if engine == 'own':
                args = ['--repo', str(root), '--contract', str(root / 'contract.json'), '--out', 'submission']
            else:
                args = ['--repo', str(root), '--input', str(root / 'dataset/inputs.csv'),
                        '--key', 'message_id', '--columns', 'message_id,action,reason',
                        '--allowed', 'action=notify,digest', '--transcript', 'log.txt', '--out', 'submission']
            result, raw = process([sys.executable, '-I', '-B', str(script)] + args, root)
            # Each script documents its own normal refusal codes. Tracebacks and
            # timeouts never count as detecting a defect.
            known = (0, 1, 2, 3) if engine == 'own' else (0, 1)
            status = ('UNKNOWN' if result['returncode'] not in known or result.get('crashed')
                      or result.get('oversized') else 'PASS' if result['returncode'] == 0 else 'FAIL')
        else:
            result, raw = process([sys.executable, '-I', '-B', str(HERE / 'worker.py'),
                                   '--repo', str(repo), '--fixture', str(root), '--engine', engine,
                                   '--audit', own_audit], root)
            try:
                status = json.loads(raw)['status'] if result['returncode'] == 0 else 'UNKNOWN'
            except (ValueError, KeyError):
                status = 'UNKNOWN'
        return dict(result, id=case['id'], category=case['category'], defect=case['defect'],
                    actual=status, expected='FAIL' if case['defect'] else 'PASS', input_sha256=hashes,
                    requires=case.get('requires'),
                    policy_support='N/A' if engine == 'competitor' and case.get('requires') else 'SUPPORTED')


def rates(rows):
    eligible = [r for r in rows if r.get('policy_support') != 'N/A']
    healthy = [r for r in eligible if not r['defect'] and r['actual'] in ('PASS', 'FAIL')]
    defective = [r for r in eligible if r['defect'] and r['actual'] in ('PASS', 'FAIL')]
    fp = sum(r['actual'] == 'FAIL' for r in healthy)
    fn = sum(r['actual'] == 'PASS' for r in defective)
    return {'healthy_executed': len(healthy), 'defective_executed': len(defective),
            'false_positives': fp, 'false_negatives': fn,
            'false_positive_rate': fp / len(healthy) if healthy else None,
            'false_negative_rate': fn / len(defective) if defective else None,
            'unknown': sum(r['actual'] == 'UNKNOWN' for r in eligible),
            'not_applicable': len(rows) - len(eligible),
            'seconds_total': sum(r['seconds'] for r in rows)}


def discovery(repo):
    files = sorted(repo.glob('skills/*/SKILL.md'))
    if (repo / 'hackerrank-orchestrate/SKILL.md').is_file():
        files.append(repo / 'hackerrank-orchestrate/SKILL.md')
    return {'file_discovery': 'PASS' if files else 'FAIL',
            'files': [p.relative_to(repo).as_posix() for p in files],
            'live_activation': 'UNKNOWN', 'reason': 'No actual agent runtime invoked.'}


def installation(repo, engine):
    with tempfile.TemporaryDirectory(prefix='orchestrate-install-comparison-') as temp:
        root = Path(temp).resolve()
        # Canonical folder names differ; this is the declared adapter mapping.
        name = 'hackerrank-orchestrate' if engine == 'own' else 'orchestrate'
        dest = root / ('.claude/skills' if engine == 'own' else 'skills')
        sentinel = dest / name / 'custom.txt'
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b'USER CONTENT\n')
        if engine == 'own':
            # The conflict must be on an output file, not an unrelated sidecar.
            conflict = sentinel.parent / 'SKILL.md'
            conflict.write_bytes(b'USER SKILL\n')
            argv = [sys.executable, '-B', '-m', 'orchestrate_toolkit', 'install', '--agent', 'claude',
                    '--project', str(root)]
        else:
            conflict = sentinel.parent / 'SKILL.md'
            conflict.write_bytes(b'USER SKILL\n')
            if os.name == 'nt':
                host = shutil.which('powershell') or shutil.which('pwsh')
                argv = [host, '-NoProfile', '-NonInteractive', '-File', str(repo / 'scripts/install-skills.ps1'),
                        '-Dest', str(dest)] if host else None
            else:
                host = shutil.which('bash')
                argv = [host, str(repo / 'scripts/install-skills.sh'), '--dest', str(dest)] if host else None
            if argv is None:
                return {'conflict_preservation': 'UNKNOWN', 'reason': 'Installer host unavailable.'}
        # All replacement/deletion by the inspected competitor installer stays in
        # this newly allocated temp destination. Never pass a real home folder.
        dest.resolve().relative_to(root)
        result, raw = process(argv, repo, timeout=120, home=root)
        preserved = sentinel.is_file() and sentinel.read_bytes() == b'USER CONTENT\n'
        preserved = preserved and conflict.is_file() and conflict.read_bytes() == b'USER SKILL\n'
        normal = (result['returncode'] == 0 if engine == 'competitor' else
                  result['returncode'] == 0 or result['returncode'] == 2 and b'unowned file conflict' in raw)
        normal = normal and not result.get('crashed') and not result.get('oversized')
        return dict(result, conflict_preservation='UNKNOWN' if not normal else 'PASS' if preserved else 'FAIL',
                    dry_run='N/A' if engine == 'competitor' else 'UNKNOWN',
                    note='Single existing-folder conflict; lifecycle/idempotency not measured here.')


def compare(own, competitor=None, allow_competitor=False, own_audit='corpus_literals'):
    suite = fixtures()
    engines = {'own': own}
    if competitor is not None and allow_competitor:
        engines['competitor'] = competitor
    reports = {}
    for engine, repo in engines.items():
        rows = [run_case(repo, engine, suite, case, own_audit) for case in suite['cases']]
        reports[engine] = {'source': revision(repo, [OWN_PACKAGE if engine == 'own' else OTHER_PACKAGE,
                             'hackerrank-orchestrate/scripts/corpus_literals.py' if engine == 'own' else
                             'orchestrate_kit/evaluator/plugins/orchestrate/leakage.py',
                             'orchestrate_toolkit/audits.py']),
                           'cases': rows,
                           'metrics': {cat: rates([r for r in rows if r['category'] == cat])
                                       for cat in ('packaging', 'leakage')},
                           'common_interface_metrics': {
                               cat: rates([r for r in rows if r['category'] == cat and not r['requires']])
                               for cat in ('packaging', 'leakage')},
                           'capabilities': {'required_usage': 'SUPPORTED' if engine == 'own' else 'N/A',
                                            'sidecar_policy': 'SUPPORTED' if engine == 'own' else 'N/A',
                                            'idempotency': 'UNKNOWN', 'backups': 'UNKNOWN',
                                            'uninstall': 'UNKNOWN', 'live_activation': 'UNKNOWN'},
                           'discovery': discovery(repo), 'installation': installation(repo, engine)}
    if 'competitor' not in reports:
        reports['competitor'] = {'status': 'UNKNOWN', 'reason': 'Not supplied or execution not authorized.'}
    return {'schema_version': 1, 'kind': 'synthetic_comparison',
            'environment': {'python': platform.python_version(), 'platform': platform.platform()},
            'suite_sha256': sha((HERE / 'fixtures.json').read_bytes()),
            'runner_sha256': sha(Path(__file__).read_bytes()),
            'worker_sha256': sha((HERE / 'worker.py').read_bytes()), 'engines': reports,
            'own_leakage_audit': own_audit,
            'official_score': 'UNKNOWN', 'overall_superiority': 'UNKNOWN',
            'boundary': 'Synthetic diagnostic only. Installation paths are mapped; live activation and adversarial model behavior untested.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--own', type=Path, default=ROOT)
    parser.add_argument('--competitor', type=Path)
    parser.add_argument('--allow-competitor-exec', action='store_true')
    parser.add_argument('--own-leakage-audit', choices=['corpus_literals', 'decision_ids'], default='corpus_literals')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        parser.error('report must be a new file in an existing directory')
    result = compare(args.own.resolve(), args.competitor.resolve() if args.competitor else None,
                     args.allow_competitor_exec, args.own_leakage_audit)
    with args.report.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: v.get('metrics', v) for k, v in result['engines'].items()}, indent=2))
    # Diagnostic findings are data, not a successful quality gate. CI separately
    # asserts our expected controls; competitor failures never break our build.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
