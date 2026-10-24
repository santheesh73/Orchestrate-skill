"""Confined filesystem operations, bounded JSON and exclusive local transactions."""

import contextlib
import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 32 * 1024 * 1024


class ToolkitError(Exception):
    """A recoverable input, ownership or permission error."""


def source_root():
    root = Path(__file__).resolve().parents[1]
    return root if (root / 'hackerrank-orchestrate/SKILL.md').is_file() else Path(__file__).parent / 'resources'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def project(path):
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ToolkitError('project must be an existing directory')
    return root


def relative(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ToolkitError('expected a portable relative path')
    if any(ord(c) < 32 or c in ':*?"<>|' for c in name):
        raise ToolkitError('invalid path character')
    parts = name.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts):
        raise ToolkitError('unsafe path component')
    devices = {'con', 'prn', 'aux', 'nul'} | {a + str(n) for a in ('com', 'lpt') for n in range(1, 10)}
    if any(p.casefold().split('.')[0] in devices for p in parts):
        raise ToolkitError('reserved device path')
    return name


def confined(root, name):
    target = root
    for part in relative(name).split('/'):
        target = target / part
        if target.is_symlink() or getattr(target, 'is_junction', lambda: False)():
            raise ToolkitError('symlink/junction path refused: ' + name)
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise ToolkitError('path escapes project') from None
    return target


def read_bytes(path, limit=MAX_BYTES):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ToolkitError('expected regular file: ' + path.name)
    with path.open('rb') as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ToolkitError('file exceeds size limit: ' + path.name)
    return content


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ToolkitError('duplicate JSON key')
        result[key] = value
    return result


def read_json(path):
    return json.loads(read_bytes(path, 2 * 1024 * 1024).decode('utf-8-sig'), object_pairs_hook=pairs)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def write_new(path, data):
    """No-clobber write. The caller has already confined path and created parents."""
    with path.open('xb') as stream:
        stream.write(data)


def atomic_replace(path, data):
    """Replace only a caller-verified owned state file in its existing parent."""
    handle, name = tempfile.mkstemp(prefix='.orchestrate-', dir=str(path.parent))
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def operation(root):
    directory = confined(root, '.orchestrate')
    directory.mkdir(exist_ok=True)
    lock = confined(root, '.orchestrate/operation.lock')
    try:
        write_new(lock, json_bytes({'pid': os.getpid(), 'started': now()}))
    except FileExistsError:
        raise ToolkitError('another operation or stale lock exists; inspect operation.lock before recovery') from None
    try:
        yield
    finally:
        lock.unlink()


def sha_string(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None
