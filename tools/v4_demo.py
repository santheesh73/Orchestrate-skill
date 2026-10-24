#!/usr/bin/env python3
"""Exercise V4 end to end in a fresh synthetic project with actual local runs.

Failure it prevents: independently passing modules that cannot complete the
analysis-to-package workflow together. This runs only the bundled offline fixture,
never user-selected candidate code or an agent model. No official readiness claim.
"""

import argparse
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import assessment, challenge, evaluation, interview, memory, mentor, records, release, scoring, workflow
from orchestrate_toolkit.common import json_bytes


def run(root):
    shutil.copytree(ROOT / 'examples/offline', root,
                    ignore=shutil.ignore_patterns('.orchestrate', 'evaluation', '__pycache__'))
    root = root.resolve()

    def write(name, value):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else json_bytes(value))

    write('AGENTS.md', 'Fictional offline fixture. Preserve instructions and input.csv. No competition transcript is claimed.\n')
    write('GEMINI.md', '@AGENTS.md\n')
    write('problem_statement.md', 'Build the bundled deterministic fixture. Output columns id,status; permitted status values ok and review. Every input row is required.\n')
    write('DESIGN.md', '# Fictional design\nAlternative: a model is unnecessary for this deterministic fixture.\nFailure handling: validate CSV before packaging.\nUncertainty: no agent behavior or official scores are evaluated.\nTests: exact contract, independent replay and injected invalid enum.\n')
    command = [sys.executable, str(root / 'main.py')]
    first = subprocess.run(command, cwd=str(root), capture_output=True, timeout=30)
    if first.returncode:
        raise RuntimeError('bundled offline producer failed')
    shutil.copy2(root / 'output.csv', root / 'first-run.csv')
    second = subprocess.run(command, cwd=str(root), capture_output=True, timeout=30)
    if second.returncode:
        raise RuntimeError('bundled offline replay failed')
    write('evaluation.json', {'contract': 'contract.json', 'replay': 'first-run.csv'})
    contract = records.load(root, 'contract.json')
    bad = dict(contract, output='invalid-output.csv', artifacts={'output.csv': 'invalid-output.csv'})
    write('invalid-contract.json', bad)
    with (root / 'output.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.reader(stream))
    mutated = [list(row) for row in rows]
    mutated[1][1] = 'invalid-enum'
    buffer = io.StringIO(newline='')
    csv.writer(buffer).writerows(mutated)
    write('invalid-output.csv', buffer.getvalue())
    write('negative-evaluation.json', {'contract': 'invalid-contract.json'})
    write('assessment.json', {'evaluation': 'evaluation.json',
        'inputs': [{'path': 'input.csv', 'columns': ['id', 'value'], 'id_column': 'id', 'nonempty': ['value']}],
        'relations': [{'kind': 'equal_csv', 'first': 'first-run.csv', 'second': 'output.csv', 'id_column': 'id'}],
        'controls': [{'name': 'injected enum', 'config': 'negative-evaluation.json', 'expected': 'FAIL', 'category': 'mutation'}]})
    analyzed = challenge.analyze(root)
    write('.orchestrate/reports/challenge.json', analyzed)
    evaluated = assessment.assess(root, 'assessment.json')
    write('.orchestrate/reports/evaluation.json', evaluated)
    negative = evaluation.evaluate(root, 'negative-evaluation.json')
    write('baseline-metrics.json', {'metrics': {'contract_failures': int(negative['overall'] == 'FAIL')},
                                  'failures': ['injected enum'], 'checks': ['FAIL']})
    write('candidate-metrics.json', {'metrics': {'contract_failures': int(evaluated['overall'] != 'PASS')},
                                   'failures': [], 'checks': [evaluated['overall']]})
    write('experiment.json', {'id': 'synthetic-demo', 'hypothesis': 'An injected invalid enum is rejected while the valid fixture passes.',
        'code_revision': 'synthetic-local-fixture', 'dataset': ['input.csv'], 'sources': ['main.py'],
        'configuration': {'origin': 'synthetic', 'model_calls': 0}, 'baseline': 'baseline-metrics.json',
        'candidate': 'candidate-metrics.json', 'directions': {'contract_failures': 'lower'},
        'reconsideration': 'Use independent genuine agent trials before claiming skill effectiveness.'})
    experiment = memory.create(root, 'experiment.json')
    write('decision.json', {'decision': 'DEFER', 'reason': 'Synthetic sensitivity is not evidence of live-agent gains.',
                            'reconsideration': 'Run genuine repeated paired trials.'})
    memory.decide(root, 'synthetic-demo', 'decision.json')
    advised = mentor.review(root, '.orchestrate/reports/evaluation.json', 'DESIGN.md', 'synthetic-demo')
    questions = interview.prepare(root, ['main.py'], '.orchestrate/reports/evaluation.json', 'synthetic-demo')
    write('scoring.json', {'assumptions': 'Fictional local shape signal only. Interview is unmeasured.', 'dimensions': [
        {'name': 'shape', 'weight': 0.6, 'criterion_origin': 'local_heuristic', 'evidence': '.orchestrate/reports/evaluation.json', 'check': 'contract'},
        {'name': 'interview', 'weight': 0.4, 'criterion_origin': 'unmeasured'}]})
    estimated = scoring.estimate(root, 'scoring.json')
    write('reproduction.json', {'kind': 'reproducibility', 'status': 'PASS',
        'reviewer': 'SYNTHETIC DEMO CONTROLLER; NOT A PARTICIPANT REVIEW', 'bound_sources': evaluated['bound_sources'],
        'procedure': 'Two actual runs of the trusted bundled fixture in this fresh directory; independently saved first output.',
        'commands': [{'argv': ['python', 'main.py'], 'returncode': first.returncode},
                     {'argv': ['python', 'main.py'], 'returncode': second.returncode}]})
    write('release.json', {'contract': 'contract.json', 'evaluation': '.orchestrate/reports/evaluation.json',
        'reproducibility': 'reproduction.json', 'dependencies': {'mode': 'standard-library'},
        'required_files': [], 'manual': []})
    gated = release.gate(root, 'release.json')
    write('.orchestrate/reports/release.json', gated)
    write('policy.json', {'schema_version': 1, 'required_files': {'ANALYZE': ['.orchestrate/reports/challenge.json'],
                                                             'PLAN': ['DESIGN.md']}, 'release_gate': 'release.json'})
    workflow.init(root, 'policy.json')
    for state in workflow.STATES[1:-1]:
        workflow.advance(root, state, '.orchestrate/reports/evaluation.json' if state in ('TEST', 'EVALUATE', 'VALIDATE') else 'DESIGN.md')
    package = evaluation.module('v4_demo_package', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
    with contextlib_redirect():
        package.build(root, root / 'contract.json', '.orchestrate/submission')
    workflow.advance(root, 'SUBMIT', '.orchestrate/submission/manifest.json', approve_submit=True)
    checks = {'participant_contract': evaluated['overall'],
              'injected_defect': 'PASS' if negative['overall'] == 'FAIL' else 'FAIL',
              'missing_score_not_filled': 'PASS' if estimated['estimate'] is None else 'FAIL',
              'mentor_honesty': 'PASS' if advised['overall'] == 'UNKNOWN' else 'FAIL',
              'interview_questions': 'PASS' if questions['questions'] else 'FAIL',
              'local_release': gated['overall'],
              'workflow': 'PASS' if workflow.load(root)['state'] == 'SUBMIT' else 'FAIL'}
    return {'schema_version': 1, 'kind': 'v4_synthetic_integration_demo', 'origin': 'synthetic',
            'overall': records.status(checks.values()), 'checks': checks,
            'experiment_recommendation': experiment['recommendation'], 'score': estimated,
            'live_agent_verification': 'UNKNOWN', 'official_acceptance': 'UNKNOWN',
            'boundary': 'Actual local fixture runs, supplied synthetic review records, no agent invocation or participant transcript.'}


def contextlib_redirect():
    import contextlib
    return contextlib.redirect_stdout(io.StringIO())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, help='new directory for persistent synthetic outputs; default uses a temporary directory')
    args = parser.parse_args(argv)
    if args.project:
        target = args.project.expanduser().absolute()
        if any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in (target,) + tuple(target.parents)):
            parser.error('linked destination refused')
        if target.exists():
            parser.error('project must be new; existing directories are never replaced')
        report = run(target)
    else:
        with tempfile.TemporaryDirectory(prefix='orchestrate-v4-demo-') as temp:
            report = run(Path(temp).resolve() / 'project')
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report['overall'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
