#!/usr/bin/env python3
"""Build a new submission bundle from an explicit JSON contract.

Failure it prevents: a false readiness verdict on empty data or missing required
files, and accidentally archiving a working tree or overwriting an earlier bundle.
Only standard-library Python 3.9+ is used. Target code is never executed.
Exit 0: checks/build succeeded; 1: contract violation; 2: bad config/path/I/O;
3: UNKNOWN because there are no data rows. No published output on failure.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_FIELD = 1024 * 1024
FORBIDDEN_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
                  'node_modules', '.claude', '.agents', '.codex', '.aws', '.ssh', '.azure'}
SECRET_RE = re.compile(
    r'sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|'
    r'(?i:(?:api[_-]?key|secret|token)\s*=\s*[\'"][^\'"\r\n]{12,}[\'"])')
REQUIRED = {'input', 'output', 'id_column', 'columns', 'require_order',
            'code_files', 'required_code_files', 'artifacts'}
OPTIONAL = {'enums', 'allow_blank', 'hashes'}


class Invalid(Exception):
    """An invalid config, inaccessible path or unsupported input."""


class Violation(Exception):
    """Configured submission requirements did not hold."""


class Unknown(Exception):
    """Insufficient data to verify a submission."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('duplicate JSON key: ' + key)
        result[key] = value
    return result


def path_name(value):
    """Portable exact relative names, with no traversal or device names."""
    if not isinstance(value, str) or not value or '\\' in value:
        raise Invalid('paths must be nonempty relative strings using /')
    if any(ord(c) < 32 or c in ':*?"<>|' for c in value):
        raise Invalid('path contains a forbidden character')
    parts = value.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts):
        raise Invalid('path has empty, traversal or nonportable components')
    reserved = {'con', 'prn', 'aux', 'nul'} | {
        prefix + str(n) for prefix in ('com', 'lpt') for n in range(1, 10)}
    if any(p.split('.')[0].casefold() in reserved for p in parts):
        raise Invalid('path uses a reserved device name')
    return value


def names(values, label, allow_empty=False):
    if not isinstance(values, list) or (not values and not allow_empty):
        raise Invalid(label + ' must be a list' + ('' if allow_empty else ' with entries'))
    if any(not isinstance(v, str) or not v.strip() for v in values):
        raise Invalid(label + ' must contain nonempty strings')
    if len(values) != len(set(values)):
        raise Invalid(label + ' contains duplicates')
    return values


def collision_check(values):
    seen = set()
    for value in values:
        key = path_name(value).casefold()
        parts = PurePosixPath(key).parts
        parents = {'/'.join(parts[:i]) for i in range(1, len(parts))}
        if key in seen or parents & seen or any(p.startswith(key + '/') for p in seen):
            raise Invalid('colliding archive or artifact paths: ' + value)
        seen.add(key)


def safe_source(repo, name):
    current = repo
    for part in path_name(name).split('/'):
        current = current / part
        if current.is_symlink():
            raise Invalid('symlinks are not accepted: ' + name)
    try:
        current.resolve().relative_to(repo)
    except ValueError:
        raise Invalid('source resolves outside project: ' + name) from None
    if not stat.S_ISREG(current.stat().st_mode):
        raise Invalid('source is not a regular file: ' + name)
    return current


def forbidden(name, code=False):
    parts = [p.casefold() for p in PurePosixPath(name).parts]
    base = parts[-1]
    return (any(p in FORBIDDEN_DIRS for p in parts)
            or code and 'dataset' in parts
            or base == '.env' or base.startswith('.env.')
            or base in {'id_rsa', 'id_ed25519', 'credentials', 'credentials.json'}
            or PurePosixPath(base).suffix in {'.pem', '.key', '.p12', '.pfx'})


def load_contract(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise Invalid('contract must be a regular file, not a symlink')
    if path.stat().st_size > MAX_FIELD:
        raise Invalid('contract is too large')
    data = path.read_bytes()
    config = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique_object)
    if not isinstance(config, dict):
        raise Invalid('contract must be a JSON object')
    if REQUIRED - config.keys() or config.keys() - REQUIRED - OPTIONAL:
        raise Invalid('missing or unknown contract keys: ' + str(sorted(
            (REQUIRED - config.keys()) | (config.keys() - REQUIRED - OPTIONAL))))
    for key in ('input', 'output'):
        path_name(config[key])
    if config['input'] == config['output']:
        raise Invalid('input and output must be different files')
    columns = names(config['columns'], 'columns')
    key = config['id_column']
    if not isinstance(key, str) or key not in columns:
        raise Invalid('id_column must be an output column')
    if type(config['require_order']) is not bool:
        raise Invalid('require_order must be boolean')
    blank = names(config.get('allow_blank', []), 'allow_blank', allow_empty=True)
    if set(blank) - set(columns) or key in blank:
        raise Invalid('allow_blank must name output columns other than the ID')
    enums = config.get('enums', {})
    if not isinstance(enums, dict) or set(enums) - set(columns):
        raise Invalid('enums must map output columns to allowed strings')
    for col, values in enums.items():
        names(values, 'enum ' + col)
    code = names(config['code_files'], 'code_files')
    required = names(config['required_code_files'], 'required_code_files', allow_empty=True)
    for name in code + required:
        path_name(name)
    if set(required) - set(code):
        raise Violation('required_code_files missing from code_files')
    collision_check(code)
    artifacts = config['artifacts']
    if not isinstance(artifacts, dict) or not artifacts:
        raise Invalid('artifacts must map destinations to source paths')
    for dest, source in artifacts.items():
        path_name(dest)
        path_name(source)
        if forbidden(dest) or forbidden(source):
            raise Invalid('credential or environment path in artifacts')
    collision_check(list(artifacts) + ['code.zip', 'manifest.json'])
    if config['output'] not in artifacts.values():
        raise Violation('artifacts must include the final output CSV')
    if any(forbidden(name, code=True) for name in code):
        raise Invalid('forbidden code archive path')
    hashes = config.get('hashes', {})
    sources = {config['input'], config['output']} | set(code) | set(artifacts.values())
    if not isinstance(hashes, dict) or set(hashes) - sources:
        raise Invalid('hashes must map selected sources to SHA-256 strings')
    for value in hashes.values():
        if not isinstance(value, str) or not re.fullmatch('[a-fA-F0-9]{64}', value):
            raise Invalid('invalid SHA-256 in hashes')
    return config, data, sources


def snapshot(repo, sources):
    total, result = 0, {}
    for name in sorted(sources):
        path = safe_source(repo, name)
        if path.stat().st_size > MAX_FILE:
            raise Invalid('file exceeds size limit: ' + name)
        with path.open('rb') as stream:
            data = stream.read(MAX_FILE + 1)
        if not data:
            raise Violation('required source is empty: ' + name)
        total += len(data)
        if len(data) > MAX_FILE or total > MAX_TOTAL:
            raise Invalid('source snapshot exceeds size limit')
        result[name] = data
    return result


def read_csv(data, label):
    text = data.decode('utf-8-sig')
    if '\x00' in text:
        raise Violation(label + ' contains NUL bytes')
    previous = csv.field_size_limit(MAX_FIELD)
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader, [])
        if not header or len(header) != len(set(header)) or any(not c.strip() for c in header):
            raise Violation(label + ' has invalid or duplicate headers')
        rows = []
        for row in reader:
            if len(row) != len(header):
                raise Violation(label + ' has a ragged record')
            rows.append(dict(zip(header, row)))
        return header, rows
    finally:
        csv.field_size_limit(previous)


def verify_csv(config, data):
    in_header, inputs = read_csv(data[config['input']], 'input')
    out_header, outputs = read_csv(data[config['output']], 'output')
    key = config['id_column']
    if key not in in_header or out_header != config['columns']:
        raise Violation('input ID column or exact output header does not match')
    ids = []
    for label, rows in [('input', inputs), ('output', outputs)]:
        values = [row[key] for row in rows]
        if any(not v.strip() for v in values) or len(values) != len(set(values)):
            raise Violation(label + ' has blank or duplicate IDs')
        ids.append(values)
    if set(ids[0]) != set(ids[1]):
        raise Violation('output ID coverage does not match input')
    if config['require_order'] and ids[0] != ids[1]:
        raise Violation('output order differs from required input order')
    blank = set(config.get('allow_blank', []))
    for row in outputs:
        for col, value in row.items():
            if not value.strip():
                if col not in blank:
                    raise Violation('blank required output field: ' + col)
                continue
            if col in config.get('enums', {}) and value not in config['enums'][col]:
                raise Violation('output enum violation: ' + col)
    if not inputs or not outputs:
        raise Unknown('no data rows; coverage and correctness cannot be verified')
    return len(outputs)


def destination(repo, requested, sources, contract):
    raw = Path(requested)
    raw = raw if raw.is_absolute() else repo / raw
    # Reject links in every existing destination component before resolving it.
    for part in [raw] + list(raw.parents):
        if part.is_symlink():
            raise Invalid('output path contains a symlink')
    out = raw.resolve()
    if out.exists():
        raise Invalid('output already exists; choose a new directory')
    if not out.parent.is_dir():
        raise Invalid('output parent must already exist')
    for source in list(sources) + [contract]:
        if source == out or out in source.parents:
            raise Invalid('output overlaps an input')
    if out == repo or out in repo.parents:
        raise Invalid('output overlaps the project')
    return out


def build(repo, contract, requested, check_only=False):
    config, contract_data, sources = load_contract(contract)
    out = destination(repo, requested,
                      [repo / name for name in sources], contract.resolve())
    data = snapshot(repo, sources)
    # Input and output may have different names yet refer to the same hardlinked file.
    if os.path.samefile(repo / config['input'], repo / config['output']):
        raise Invalid('input and output refer to the same file')
    rows = verify_csv(config, data)
    for name, expected in config.get('hashes', {}).items():
        if sha(data[name]) != expected.lower():
            raise Violation('final-run hash mismatch: ' + name)
    shipped = set(config['code_files']) | set(config['artifacts'].values())
    for name in sorted(shipped):
        # Scan decodable text regardless of extension, without printing secret values.
        try:
            text = data[name].decode('utf-8')
        except UnicodeDecodeError:
            continue
        if SECRET_RE.search(text):
            raise Violation('possible secret in selected file: ' + name)
    print('CHECKED: exact CSV contract, %d data rows, required files and archive scope' % rows)
    if check_only:
        print('CHECK ONLY: no files written; quality and provenance review remain manual')
        return
    staging = Path(tempfile.mkdtemp(prefix='.submission-', dir=str(out.parent)))
    try:
        archive = staging / 'code.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for name in sorted(config['code_files']):
                # Fixed metadata makes identical snapshots produce identical archives.
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = (stat.S_IFREG | 0o644) << 16
                bundle.writestr(entry, data[name])
        for dest, source in config['artifacts'].items():
            target = staging / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data[source])
        manifest = {
            'schema_version': 1, 'rows': rows, 'contract_sha256': sha(contract_data),
            'source_sha256': {name: sha(value) for name, value in sorted(data.items())},
            'archive_members': {name: sha(data[name]) for name in sorted(config['code_files'])},
            'artifact_sources': config['artifacts'],
            'bundle_sha256': {p.relative_to(staging).as_posix(): sha(p.read_bytes())
                              for p in sorted(staging.rglob('*')) if p.is_file()},
            'verification': 'Configured shape and files only; manual quality, contract and clean-run review required.'}
        (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        if out.exists() or out.is_symlink():
            raise Invalid('output appeared during build; nothing replaced')
        os.rename(staging, out)
        print('PACKAGE BUILT: ' + str(out))
        print('Manifest: ' + str(out / 'manifest.json'))
        print('Manual contract, clean-run and quality review still required.')
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--out', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        if not repo.is_dir():
            raise Invalid('repo must be a directory')
        build(repo, args.contract, args.out, args.check_only)
        return 0
    except Unknown as exc:
        print('UNKNOWN: ' + str(exc), file=sys.stderr)
        return 3
    except Violation as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1
    except (Invalid, OSError, ValueError, csv.Error, RecursionError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='backslashreplace')
    sys.exit(main())
