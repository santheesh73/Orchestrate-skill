"""Immutable local experiment snapshots and append-only, source-linked decisions."""

import platform
import re
from . import records
from .common import ToolkitError, confined, digest, json_bytes, now, operation, write_new

DIRECTORY = '.orchestrate/memory'


def identity(value):
    if not isinstance(value, str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}', value):
        raise ToolkitError('experiment ID must be lowercase letters, digits and hyphens')
    return value


def metric_record(root, name):
    value = records.schema(records.load(root, name), ('metrics', 'failures', 'checks'))
    if not isinstance(value['metrics'], dict):
        raise ToolkitError('metrics must be a numeric mapping')
    for key, number in value['metrics'].items():
        records.text(key)
        records.finite(number)
    for failure in records.sequence(value['failures']):
        records.text(failure)
    for state in records.sequence(value['checks']):
        if state not in records.STATES:
            raise ToolkitError('invalid experiment check status')
    return value


def create(root, config_name):
    config = records.schema(records.load(root, config_name),
        ('id', 'hypothesis', 'code_revision', 'dataset', 'sources', 'configuration',
         'baseline', 'candidate', 'directions', 'reconsideration'))
    ident = identity(config['id'])
    for key in ('hypothesis', 'code_revision', 'reconsideration'):
        records.text(config[key])
    if not isinstance(config['configuration'], dict) or not isinstance(config['directions'], dict):
        raise ToolkitError('experiment configuration/directions must be mappings')
    dataset = records.sequence(config['dataset'])
    sources = records.sequence(config['sources'])
    if not dataset or not sources:
        raise ToolkitError('experiment needs dataset and implementation fingerprints')
    baseline = metric_record(root, config['baseline'])
    candidate = metric_record(root, config['candidate'])
    deltas, regressions, improvements = {}, [], []
    keys = set(baseline['metrics']) | set(candidate['metrics'])
    missing = keys - (set(baseline['metrics']) & set(candidate['metrics']) & set(config['directions']))
    if set(config['directions']) - keys or any(d not in ('higher', 'lower') for d in config['directions'].values()):
        raise ToolkitError('metric directions must reference actual metrics and be higher/lower')
    for key in sorted(keys - missing):
        delta = candidate['metrics'][key] - baseline['metrics'][key]
        deltas[key] = delta
        signed = delta if config['directions'][key] == 'higher' else -delta
        (improvements if signed > 0 else regressions if signed < 0 else []).append(key)
    new_failures = sorted(set(candidate['failures']) - set(baseline['failures']))
    checks = records.status(candidate['checks'])
    recommendation = ('ROLLBACK_RECOMMENDED' if regressions or new_failures or checks == 'FAIL' else
                      'UNKNOWN' if missing or not keys or checks != 'PASS' else 'REVIEW')
    names = [config_name, config['baseline'], config['candidate']] + dataset + sources
    hashes = records.bound(root, names)
    value = {'schema_version': 1, 'kind': 'experiment', 'id': ident, 'at': now(),
             'hypothesis': config['hypothesis'], 'code_revision': config['code_revision'],
             'revision_evidence': 'SUPPLIED; file fingerprints are recorded independently',
             'configuration': config['configuration'],
             'environment': {'python': platform.python_version(), 'platform': platform.platform()},
             'dataset_sha256': {name: hashes[name] for name in dataset}, 'bound_sources': hashes,
             'baseline': baseline, 'candidate': candidate, 'deltas': deltas,
             'directions': config['directions'],
             'regressions': regressions, 'improvements': improvements, 'new_failures': new_failures,
             'missing_metrics': sorted(missing), 'recommendation': recommendation,
             'reconsideration': config['reconsideration'], 'decision': 'UNDECIDED',
             'measurement_boundary': 'Supplied metrics and check records; no model or candidate program was executed.'}
    from .security import scan_text
    if scan_text(json_bytes(value).decode('utf-8')):
        raise ToolkitError('possible credential in experiment metadata; no record written')
    with operation(root):
        target = confined(root, DIRECTORY + '/' + ident + '.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        write_new(target, json_bytes(value))
    return value


def get(root, ident):
    name = DIRECTORY + '/' + identity(ident) + '.json'
    value = records.load(root, name)
    if not isinstance(value, dict) or value.get('kind') != 'experiment' or value.get('id') != ident:
        raise ToolkitError('invalid experiment record')
    return value


def history(root, ident):
    experiment = get(root, ident)
    directory = confined(root, DIRECTORY + '/' + ident + '.decisions')
    decisions = []
    previous = None
    if directory.exists():
        paths = sorted(directory.glob('*.json'))
        if len(paths) > 1000:
            raise ToolkitError('decision history exceeds bound')
        for path in paths:
            row = records.load(root, path.relative_to(root).as_posix())
            if row.get('experiment_sha256') != digest(json_bytes(experiment)) or row.get('previous_sha256') != previous:
                raise ToolkitError('decision history is inconsistent')
            previous = digest(json_bytes(row))
            decisions.append(row)
    return {'schema_version': 1, 'kind': 'experiment_history', 'overall': 'UNKNOWN',
            'experiment': experiment, 'decisions': decisions,
            'current_source_status': records.current(root, experiment['bound_sources'])}


def decide(root, ident, config_name):
    decision = records.schema(records.load(root, config_name), ('decision', 'reason', 'reconsideration'))
    if decision['decision'] not in ('ACCEPT', 'REJECT', 'DEFER'):
        raise ToolkitError('decision must be ACCEPT, REJECT or DEFER')
    for key in ('reason', 'reconsideration'):
        records.text(decision[key])
    from .security import scan_text
    if scan_text(json_bytes(decision).decode('utf-8')):
        raise ToolkitError('possible credential in decision metadata; no record written')
    with operation(root):
        prior = history(root, ident)
        rows = prior['decisions']
        if len(rows) >= 1000:
            raise ToolkitError('decision history bound reached')
        row = dict(decision, at=now(), experiment_sha256=digest(json_bytes(prior['experiment'])),
                   previous_sha256=digest(json_bytes(rows[-1])) if rows else None,
                   evidence_sha256=records.bound(root, [config_name])[config_name])
        directory = confined(root, DIRECTORY + '/' + ident + '.decisions')
        directory.mkdir(exist_ok=True)
        write_new(directory / ('%04d.json' % (len(rows) + 1)), json_bytes(row))
    return row


def listing(root):
    directory = confined(root, DIRECTORY)
    paths = sorted(directory.glob('*.json')) if directory.exists() else []
    return {'schema_version': 1, 'kind': 'experiment_registry', 'overall': 'UNKNOWN' if not paths else 'PASS',
            'experiments': [get(root, path.stem) for path in paths]}


def compare(root, first, second):
    left, right = get(root, first), get(root, second)
    compatible = left['dataset_sha256'] == right['dataset_sha256'] and left['directions'] == right['directions']
    keys = set(left['candidate']['metrics']) & set(right['candidate']['metrics'])
    deltas = {key: right['candidate']['metrics'][key] - left['candidate']['metrics'][key] for key in sorted(keys)} if compatible else {}
    return {'schema_version': 1, 'kind': 'experiment_comparison', 'overall': 'UNKNOWN',
            'first': first, 'second': second, 'comparable_dataset_and_metric_policy': compatible,
            'candidate_deltas': deltas, 'environment_matches': left['environment'] == right['environment'],
            'boundary': 'Stored supplied measurements; comparability is not causal attribution or automatic acceptance.'}
