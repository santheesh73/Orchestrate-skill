"""Persistent single-agent workflow with hashed evidence and no implicit execution."""

from .common import (ToolkitError, atomic_replace, confined, digest, json_bytes,
                     now, operation, read_bytes, read_json)

STATES = ('DISCOVER', 'ANALYZE', 'PLAN', 'BUILD', 'TEST', 'EVALUATE', 'IMPROVE', 'VALIDATE', 'SUBMIT')
STATE_FILE = '.orchestrate/workflow.json'


def load(root):
    state = read_json(confined(root, STATE_FILE))
    if (not isinstance(state, dict) or state.get('schema_version') != 1
            or state.get('state') not in STATES or not isinstance(state.get('history'), list)
            or len(state['history']) > 1000 or not isinstance(state.get('starter_sha256'), dict)
            or type(state.get('failures')) is not int or not 0 <= state['failures'] <= 3
            or type(state.get('recoveries')) is not int or not 0 <= state['recoveries'] <= 3
            or state.get('project_id') != digest(str(root).encode('utf-8'))):
        raise ToolkitError('invalid or foreign workflow checkpoint')
    if set(state['starter_sha256']) - {'AGENTS.md', 'CLAUDE.md', 'problem_statement.md'}:
        raise ToolkitError('unexpected starter checkpoint path')
    if any(not isinstance(event, dict) for event in state['history']):
        raise ToolkitError('invalid workflow audit event')
    return state


def save(root, state):
    if len(state['history']) > 1000:
        raise ToolkitError('audit history bound reached; preserve this checkpoint and start a new reviewed run')
    atomic_replace(confined(root, STATE_FILE), json_bytes(state))


def init(root):
    with operation(root):
        path = confined(root, STATE_FILE)
        if path.exists():
            return load(root)
        snapshots = {}
        for name in ('AGENTS.md', 'CLAUDE.md', 'problem_statement.md'):
            source = confined(root, name)
            if source.exists():
                snapshots[name] = digest(read_bytes(source))
        state = {'schema_version': 1, 'state': 'DISCOVER', 'project_id': digest(str(root).encode('utf-8')),
                 'starter_sha256': snapshots, 'failures': 0, 'recoveries': 0,
                 'history': [{'at': now(), 'event': 'initialized', 'state': 'DISCOVER'}]}
        atomic_replace(path, json_bytes(state))
        return state


def bindings(root, hashes):
    if not isinstance(hashes, dict) or not hashes:
        raise ToolkitError('evidence has no source bindings')
    for name, expected in hashes.items():
        if digest(read_bytes(confined(root, name))) != expected:
            raise ToolkitError('evidence is stale or its source changed')


def check_evidence(root, target, name, approve_submit):
    raw = read_bytes(confined(root, name))
    if not raw.strip():
        raise ToolkitError('empty evidence cannot satisfy a gate')
    if target in ('TEST', 'EVALUATE', 'VALIDATE'):
        report = read_json(confined(root, name))
        if (not isinstance(report, dict) or report.get('kind') != 'evaluation'
                or report.get('schema_version') != 1 or report.get('overall') != 'PASS'
                or report.get('project_id') != digest(str(root).encode('utf-8'))):
            raise ToolkitError('gate needs a PASS evaluation report for this project')
        if not isinstance(report.get('checks'), dict) or not report['checks']:
            raise ToolkitError('gate report has no checks')
        if any(not isinstance(c, dict) or c.get('status') != 'PASS' for c in report['checks'].values()):
            raise ToolkitError('gate contains failed or unknown checks')
        bindings(root, report.get('bound_sources'))
    elif target == 'SUBMIT':
        if not approve_submit:
            raise ToolkitError('SUBMIT needs explicit --approve-submit; no upload will occur')
        manifest = read_json(confined(root, name))
        if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1
                or type(manifest.get('rows')) is not int or manifest['rows'] < 1
                or not isinstance(manifest.get('bundle_sha256'), dict)
                or 'code.zip' not in manifest['bundle_sha256']):
            raise ToolkitError('SUBMIT needs the hardened package manifest')
        bindings(root, manifest.get('source_sha256'))
        from pathlib import PurePosixPath
        parent = PurePosixPath(name).parent
        for member, expected in manifest['bundle_sha256'].items():
            # Validate member before joining, so ../ cannot be normalized away.
            from .common import relative
            relative(member)
            if digest(read_bytes(confined(root, (parent / member).as_posix()))) != expected:
                raise ToolkitError('package member hash mismatch')
    return digest(raw)


def advance(root, target, evidence, approve_submit=False):
    if target not in STATES:
        raise ToolkitError('unknown workflow state')
    with operation(root):
        state = load(root)
        current = STATES.index(state['state'])
        allowed = [STATES[current + 1]] if current + 1 < len(STATES) else []
        if state['state'] == 'IMPROVE':
            allowed += ['BUILD', 'TEST']
        if target not in allowed:
            raise ToolkitError('invalid transition: ' + state['state'] + ' -> ' + target)
        if state['failures'] >= 3:
            raise ToolkitError('failure bound reached; inspect and explicitly recover before continuing')
        try:
            for name, expected in state['starter_sha256'].items():
                if digest(read_bytes(confined(root, name))) != expected:
                    raise ToolkitError('competition instruction/spec checkpoint changed')
            if target == 'SUBMIT':
                validations = [h for h in state['history'] if h.get('to') == 'VALIDATE']
                if not validations:
                    raise ToolkitError('no successful validation checkpoint')
                previous = validations[-1]
                if digest(read_bytes(confined(root, previous['evidence']))) != previous['sha256']:
                    raise ToolkitError('validation report changed')
                check_evidence(root, 'VALIDATE', previous['evidence'], False)
            evidence_hash = check_evidence(root, target, evidence, approve_submit)
        except (ToolkitError, OSError, ValueError) as exc:
            state['failures'] += 1
            state['history'].append({'at': now(), 'event': 'gate_failed', 'target': target,
                                     'classification': type(exc).__name__})
            save(root, state)
            raise ToolkitError('gate failed; state preserved: ' + str(exc)) from None
        state['history'].append({'at': now(), 'event': 'advanced', 'from': state['state'],
                                 'to': target, 'evidence': evidence, 'sha256': evidence_hash})
        state['state'], state['failures'] = target, 0
        save(root, state)
        return state


def recover(root, target, reason):
    with operation(root):
        state = load(root)
        if (target not in STATES or STATES.index(target) > STATES.index(state['state'])
                or not isinstance(reason, str) or not reason.strip() or state['recoveries'] >= 3):
            raise ToolkitError('recovery needs a prior/current state, a reason, and an unused recovery allowance')
        state['history'].append({'at': now(), 'event': 'recovered', 'from': state['state'], 'to': target,
                                 'reason_sha256': digest(reason.encode('utf-8'))})
        state['state'], state['failures'] = target, 0
        state['recoveries'] += 1
        save(root, state)
        return state
