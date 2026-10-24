"""Edition-configured local release gate; missing mandatory evidence blocks READY."""

from . import evaluation, records, security
from .common import ToolkitError, confined, digest, read_bytes


def review(root, name, kind, required, requirement=None):
    path = confined(root, name)
    if not path.is_file():
        return {'status': 'UNKNOWN', 'detail': 'Required human/reproduction evidence is missing.'}
    value = records.schema(records.load(root, name), ('kind', 'status', 'reviewer', 'bound_sources'),
                           ('requirement', 'procedure', 'commands'))
    if value['kind'] != kind or value['status'] not in records.STATES:
        raise ToolkitError('unexpected review evidence kind/status')
    records.text(value['reviewer'])
    state = records.current(root, value['bound_sources'])
    if not isinstance(value['bound_sources'], dict) or not set(required).issubset(value['bound_sources']):
        state = 'UNKNOWN'
    if requirement is not None and value.get('requirement') != requirement:
        state = 'FAIL'
    if kind == 'reproducibility':
        records.text(value.get('procedure'))
        commands = records.sequence(value.get('commands'), 50)
        if not commands:
            state = 'UNKNOWN'
        for command in commands:
            records.schema(command, ('argv', 'returncode'))
            if not records.sequence(command['argv']) or any(not isinstance(a, str) for a in command['argv']):
                raise ToolkitError('reproduction record needs an argument array')
            if type(command['returncode']) is not int or command['returncode'] != 0:
                state = 'FAIL'
    return {'status': records.status([state, value['status']]),
            'detail': 'Supplied reviewed evidence; hashes are checked but execution/authorship is not authenticated.'}


def gate(root, config_name):
    config = records.schema(records.load(root, config_name),
        ('contract', 'evaluation', 'reproducibility', 'dependencies', 'required_files', 'manual'))
    checks, hashes = {}, records.bound(root, [config_name, config['contract']])
    checks['contract'], contract, data = evaluation.contract_check(root, config['contract'])
    hashes.update({name: digest(raw) for name, raw in data.items()})
    required_files = records.sequence(config['required_files'], 100)
    required = set(data) | {config['contract']} | set(required_files)
    if not data:
        checks['reproducibility'] = {'status': 'UNKNOWN', 'detail': 'A valid nonempty contract is required first.'}
    else:
        checks['reproducibility'] = review(root, config['reproducibility'], 'reproducibility', required)
    report_path = confined(root, config['evaluation'])
    if not report_path.is_file():
        checks['evaluation'] = {'status': 'UNKNOWN', 'detail': 'Final participant evaluation is missing.'}
    else:
        report, state = records.evaluation_report(root, config['evaluation'])
        if not required.issubset(report.get('bound_sources', {})):
            state = 'UNKNOWN'
        checks['evaluation'] = {'status': state, 'detail': 'Final evaluation must pass and bind all configured contract sources.'}
        hashes.update(records.bound(root, [config['evaluation']]))
    deps = records.schema(config['dependencies'], ('mode',), ('path',))
    if deps['mode'] == 'pinned':
        if not deps.get('path'):
            raise ToolkitError('pinned dependencies need a path')
        checks['dependencies'] = evaluation.requirements(root, deps['path'])
        hashes.update(records.bound(root, [deps['path']]))
    elif deps['mode'] == 'standard-library' and 'path' not in deps:
        checks['dependencies'] = {'status': checks['reproducibility']['status'],
            'detail': 'Standard-library scope is a supplied declaration tied to the reproduction review, not an import proof.'}
    else:
        raise ToolkitError('unsupported dependency mode')
    for name in required_files:
        path = confined(root, name)
        present = path.is_file() and bool(read_bytes(path).strip())
        checks['required:' + name] = {'status': 'PASS' if present else 'FAIL', 'detail': 'Edition-required file presence/nonempty check.'}
        if present:
            hashes.update(records.bound(root, [name]))
    seen = set()
    for item in records.sequence(config['manual'], 50):
        records.schema(item, ('id', 'evidence'))
        ident = records.text(item['id'])
        if ident in seen:
            raise ToolkitError('duplicate manual requirement')
        seen.add(ident)
        checks['manual:' + ident] = review(root, item['evidence'], 'manual_review', required, ident)
        if confined(root, item['evidence']).is_file():
            hashes.update(records.bound(root, [item['evidence']]))
    if confined(root, config['reproducibility']).is_file():
        hashes.update(records.bound(root, [config['reproducibility']]))
    scan_names = sorted(set(data) | {name for name in config['required_files'] if confined(root, name).is_file()})
    scan = security.scan(root, scan_names)
    checks['secrets'] = {'status': scan['overall'], 'detail': 'Redacted common-secret scan of contract and required files.',
                         'findings': scan['checks']}
    checks['source_stability'] = {'status': records.current(root, hashes), 'detail': 'All recorded sources still match the final gate snapshot.'}
    overall = records.status(check['status'] for check in checks.values())
    return {'schema_version': 1, 'kind': 'submission_release_gate', 'overall': overall,
            'readiness': 'READY' if overall == 'PASS' else 'BLOCKED', 'scope': 'LOCAL CONFIGURED GATE ONLY',
            'checks': checks, 'blockers': [name for name, check in checks.items() if check['status'] != 'PASS'],
            'reproducibility_manifest': {'schema_version': 1, 'source_sha256': hashes,
                                       'contract_sha256': hashes[config['contract']]},
            'bound_sources': hashes, 'official_acceptance': 'UNKNOWN',
            'reproduction': ['python', '-m', 'orchestrate_toolkit', 'release-gate', '--config', config_name],
            'boundary': 'No upload or code execution. Manual records are supplied attestations, not signed execution proofs.'}
