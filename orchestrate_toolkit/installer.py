"""Owned-file installation and removal; user/competition instructions are never replaced."""

import os
import re
import sys
import uuid

from .adapters import AGENTS, capability_report, render
from .common import (ToolkitError, atomic_replace, confined, digest, json_bytes,
                     now, operation, read_bytes, read_json, sha_string, write_new)

LEDGER = '.orchestrate/install.json'


def load(root, scope):
    path = confined(root, LEDGER)
    if not path.exists():
        return {'schema_version': 1, 'scope': scope, 'agents': [], 'files': {}, 'history': []}
    return validate_ledger(root, read_json(path), scope)


def validate_ledger(root, value, scope):
    """Validate restored state against the same ownership boundaries as current state."""
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'scope', 'agents', 'files', 'history'}
            or value['schema_version'] != 1 or value['scope'] != scope
            or not isinstance(value['agents'], list)
            or any(not isinstance(a, str) or a not in AGENTS for a in value['agents'])
            or len(value['agents']) != len(set(value['agents']))
            or not isinstance(value['files'], dict) or len(value['files']) > 5000
            or not isinstance(value['history'], list) or len(value['history']) > 1000):
        raise ToolkitError('invalid ownership ledger; no files changed')
    expected, owners = render(value['agents'], scope)
    if set(value['files']) - set(expected):
        raise ToolkitError('ledger contains paths outside the adapter plan')
    for name, record in value['files'].items():
        confined(root, name)
        if (not isinstance(record, dict) or set(record) != {'sha256', 'owners'}
                or not sha_string(record['sha256']) or record['owners'] != owners[name]):
            raise ToolkitError('invalid ownership entry')
    return value


def selection(requested):
    if requested == ['all']:
        return sorted(AGENTS)
    if not requested or 'all' in requested or any(a not in AGENTS for a in requested):
        raise ToolkitError('select documented agents or all alone')
    return sorted(set(requested))


def install(root, agents, scope='project', dry_run=False, upgrade=False):
    agents = selection(agents)

    def plan():
        ledger = load(root, scope)
        selected = sorted(set(ledger['agents']) | set(agents))
        data, owners = render(selected, scope)
        changes = []
        for name, content in data.items():
            path = confined(root, name)
            record = ledger['files'].get(name)
            if os.path.lexists(path):
                if not record:
                    raise ToolkitError('unowned file conflict: ' + name)
                actual = digest(read_bytes(path))
                if actual != record['sha256']:
                    raise ToolkitError('user-modified installed file; preserve and resolve manually: ' + name)
                if actual != digest(content):
                    if not upgrade:
                        raise ToolkitError('owned upgrade needs --upgrade (creates backup): ' + name)
                    changes.append(name)
            else:
                changes.append(name)
        return ledger, selected, data, owners, changes

    ledger, selected, data, owners, changes = plan()
    if dry_run:
        return {'action': 'install', 'dry_run': True, 'agents': selected, 'files_to_write': changes}
    with operation(root):
        ledger, selected, data, owners, changes = plan()
        if not changes and selected == ledger['agents']:
            return {'action': 'install', 'status': 'unchanged', 'agents': selected}
        previous = {}
        backup = None
        # Snapshot old owned bytes before writing; backups never contain user-owned files.
        for name in changes:
            path = confined(root, name)
            if path.exists():
                previous[name] = read_bytes(path)
        if previous or ledger['agents'] and changes:
            backup = '.orchestrate/backups/' + uuid.uuid4().hex
            for name, content in previous.items():
                path = confined(root, backup + '/' + name)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(content)
        written = []
        try:
            for name in changes:
                path = confined(root, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                if name in previous:
                    atomic_replace(path, data[name])
                else:
                    with path.open('xb') as stream:
                        written.append(name)
                        stream.write(data[name])
                if name not in written:
                    written.append(name)
            new = {'schema_version': 1, 'scope': scope, 'agents': selected,
                   'files': {n: {'sha256': digest(b), 'owners': owners[n]} for n, b in data.items()},
                   'history': (ledger['history'] + [{'at': now(), 'action': 'install',
                                                    'agents': agents, 'backup': backup}])[-1000:]}
            if backup:
                manifest = {'schema_version': 1, 'scope': scope, 'previous_ledger': ledger,
                            'expected_ledger_sha256': digest(json_bytes(new)), 'previous_files': sorted(previous)}
                write_new(confined(root, backup + '/restore.json'), json_bytes(manifest))
            target = confined(root, LEDGER)
            atomic_replace(target, json_bytes(new))
        except (OSError, ToolkitError):
            for name in reversed(written):
                path = confined(root, name)
                if name in previous:
                    atomic_replace(path, previous[name])
                elif path.exists():
                    path.unlink()
            raise
    return {'action': 'install', 'status': 'installed', 'agents': selected,
            'files_written': len(changes), 'backup': backup}


def restore(root, backup_id, scope='project', dry_run=False, approve=False):
    """Restore only a matching owned upgrade; edits/conflicts block the whole operation."""
    if not isinstance(backup_id, str) or not re.fullmatch('[a-f0-9]{32}', backup_id):
        raise ToolkitError('backup ID must be the 32-character ID returned by install')
    if not dry_run and not approve:
        raise ToolkitError('applying a restore needs explicit --approve-restore; preview with --dry-run')
    backup = '.orchestrate/backups/' + backup_id

    def plan():
        current = load(root, scope)
        manifest = read_json(confined(root, backup + '/restore.json'))
        if (not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'scope', 'previous_ledger', 'expected_ledger_sha256', 'previous_files'}
                or manifest['schema_version'] != 1 or manifest['scope'] != scope
                or manifest['expected_ledger_sha256'] != digest(json_bytes(current))):
            raise ToolkitError('backup does not match the current owned installation')
        previous = validate_ledger(root, manifest['previous_ledger'], scope)
        names = manifest['previous_files']
        if not isinstance(names, list) or len(names) != len(set(names)) or set(names) - set(previous['files']):
            raise ToolkitError('invalid backup member list')
        for name, record in current['files'].items():
            if digest(read_bytes(confined(root, name))) != record['sha256']:
                raise ToolkitError('modified installation blocks restoration')
        prior_bytes = {name: read_bytes(confined(root, backup + '/' + name)) for name in names}
        for name, record in previous['files'].items():
            data = prior_bytes.get(name)
            if data is None:
                if name not in current['files']:
                    raise ToolkitError('backup cannot reconstruct prior owned file')
                data = read_bytes(confined(root, name))
            if digest(data) != record['sha256']:
                raise ToolkitError('backup contents do not reconstruct prior installation')
        remove = sorted(set(current['files']) - set(previous['files']))
        return current, previous, prior_bytes, remove

    current, previous, prior_bytes, remove = plan()
    if dry_run:
        return {'action': 'restore', 'dry_run': True, 'files_to_restore': sorted(prior_bytes), 'files_to_remove': remove}
    with operation(root):
        current, previous, prior_bytes, remove = plan()
        snapshots = {name: read_bytes(confined(root, name)) for name in set(prior_bytes) | set(remove)}
        touched = []
        try:
            for name, data in prior_bytes.items():
                atomic_replace(confined(root, name), data)
                touched.append(name)
            for name in remove:
                confined(root, name).unlink()
                touched.append(name)
            previous['history'] = (previous['history'] + [{'at': now(), 'action': 'restore', 'backup': backup}])[-1000:]
            atomic_replace(confined(root, LEDGER), json_bytes(previous))
        except OSError:
            for name in reversed(touched):
                target = confined(root, name)
                if target.exists():
                    atomic_replace(target, snapshots[name])
                else:
                    write_new(target, snapshots[name])
            raise
    return {'action': 'restore', 'status': 'restored', 'agents': previous['agents'],
            'backup': backup, 'note': 'Only owned installation files changed; backup and project evidence retained.'}


def uninstall(root, agents, scope='project', dry_run=False):
    requested = selection(agents)

    def plan():
        ledger = load(root, scope)
        selected = sorted(set(ledger['agents']) - set(requested))
        _, remaining = render(selected, scope)
        remove = sorted(set(ledger['files']) - set(remaining))
        for name in remove:
            path = confined(root, name)
            if path.exists() and digest(read_bytes(path)) != ledger['files'][name]['sha256']:
                raise ToolkitError('modified installed file; nothing removed: ' + name)
        return ledger, selected, remaining, remove

    ledger, selected, remaining, remove = plan()
    if dry_run:
        return {'action': 'uninstall', 'dry_run': True, 'files_to_remove': remove, 'remaining_agents': selected}
    if not ledger['agents']:
        return {'action': 'uninstall', 'status': 'unchanged'}
    with operation(root):
        ledger, selected, remaining, remove = plan()
        snapshots = {name: read_bytes(confined(root, name)) for name in remove if confined(root, name).exists()}
        removed = []
        try:
            for name in snapshots:
                confined(root, name).unlink()
                removed.append(name)
            state = confined(root, LEDGER)
            if selected:
                ledger['agents'] = selected
                ledger['files'] = {name: dict(record, owners=remaining[name])
                                   for name, record in ledger['files'].items() if name in remaining}
                ledger['history'] = (ledger['history'] + [{'at': now(), 'action': 'uninstall',
                                                         'agents': requested}])[-1000:]
                atomic_replace(state, json_bytes(ledger))
            else:
                # Retain the operation history after removing the last adapter.
                ledger['agents'], ledger['files'] = [], {}
                ledger['history'] = (ledger['history'] + [{'at': now(), 'action': 'uninstall',
                                                         'agents': requested}])[-1000:]
                atomic_replace(state, json_bytes(ledger))
        except OSError:
            for name in removed:
                path = confined(root, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(snapshots[name])
            raise
    return {'action': 'uninstall', 'status': 'removed', 'remaining_agents': selected,
            'files_removed': len(removed), 'note': 'Unowned files, backup archives and workflow state preserved.'}


def doctor(root, scope='project'):
    ledger = load(root, scope)
    findings = []
    expected, _ = render(ledger['agents'], scope)
    for name in sorted(set(expected) - set(ledger['files'])):
        findings.append({'path': name, 'status': 'missing_ownership_record'})
    for name, record in ledger['files'].items():
        path = confined(root, name)
        if not path.exists():
            findings.append({'path': name, 'status': 'missing'})
        elif digest(read_bytes(path)) != record['sha256']:
            findings.append({'path': name, 'status': 'modified'})
    return {'schema_version': 1, 'python_supported': sys.version_info >= (3, 9),
            'installation': 'FAIL' if findings else 'PASS' if ledger['agents'] else 'UNKNOWN',
            'agents': ledger['agents'], 'findings': findings, 'compatibility': capability_report(root),
            'execution': 'No runtime was launched. Executable presence is not live verification.',
            'isolation': 'Toolkit does not provide an OS sandbox.'}
