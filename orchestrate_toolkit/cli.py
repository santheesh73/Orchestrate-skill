"""Public offline CLI; no agent, remote service or target command runs implicitly."""

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

from . import __version__, adapters, evaluation, installer, workflow
from .common import ToolkitError, confined, json_bytes, project, read_bytes, source_root, write_new


def validate_sources():
    results = []
    for folder in adapters.skill_folders():
        proc = subprocess.run([sys.executable, '-I', '-B', str(source_root() / 'tools/validate_skill.py'),
                               '--standalone', '--skill-dir', str(folder)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
                              env={k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if k in os.environ})
        results.append({'skill': folder.name, 'status': 'PASS' if proc.returncode == 0 else 'FAIL'})
    return {'schema_version': 1, 'kind': 'skill_validation',
            'overall': evaluation.worst([r['status'] for r in results]), 'skills': results}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', action='version', version=__version__)
    commands = p.add_subparsers(dest='command', required=True)
    for name in ('install', 'uninstall'):
        s = commands.add_parser(name)
        s.add_argument('--agent', action='append', required=True, choices=sorted(adapters.AGENTS) + ['all'])
        s.add_argument('--project', default='.')
        s.add_argument('--scope', choices=['project', 'user'], default='project')
        s.add_argument('--home', type=Path, help='explicit user-home directory for user scope; defaults to current home')
        s.add_argument('--dry-run', action='store_true')
        if name == 'install':
            s.add_argument('--upgrade', action='store_true', help='update unmodified owned files, creating a backup')
    for name in ('doctor', 'compatibility'):
        s = commands.add_parser(name)
        s.add_argument('--project', default='.')
        if name == 'doctor':
            s.add_argument('--scope', choices=['project', 'user'], default='project')
            s.add_argument('--home', type=Path)
    commands.add_parser('validate', help='validate all canonical skill folders without running target code')
    e = commands.add_parser('evaluate')
    e.add_argument('--project', default='.')
    e.add_argument('--config', required=True)
    e.add_argument('--report', required=True, help='new project-relative JSON report path')
    e.add_argument('--allow-exec', action='store_true', help='explicit consent to execute configured local checks; not a sandbox')
    e.add_argument('--pass-env', action='append', default=[], help='explicit environment variable to forward; values are not logged')
    w = commands.add_parser('workflow')
    w.add_argument('action', choices=['init', 'status', 'advance', 'recover'])
    w.add_argument('--project', default='.')
    w.add_argument('--to', choices=workflow.STATES)
    w.add_argument('--evidence')
    w.add_argument('--reason')
    w.add_argument('--approve-submit', action='store_true')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'validate':
            result = validate_sources()
            code = 0 if result['overall'] == 'PASS' else 1
        else:
            if getattr(args, 'scope', 'project') == 'user':
                root = project(args.home or Path.home())
            else:
                if getattr(args, 'home', None):
                    raise ToolkitError('--home requires --scope user')
                root = project(args.project)
            if args.command == 'install':
                result = installer.install(root, args.agent, args.scope, args.dry_run, args.upgrade)
            elif args.command == 'uninstall':
                result = installer.uninstall(root, args.agent, args.scope, args.dry_run)
            elif args.command == 'doctor':
                result = installer.doctor(root, args.scope)
            elif args.command == 'compatibility':
                result = {'agents': adapters.capability_report(root), 'test_evidence': 'See tests/test_universal.py and CI; live runtime UNKNOWN.'}
            elif args.command == 'evaluate':
                target = confined(root, args.report)
                if target.exists() or os.path.lexists(target):
                    raise ToolkitError('report exists; choose a new path')
                if args.report.split('/')[0].casefold() in {'.git', '.agents', '.claude', '.gemini', '.aws', '.ssh', 'dataset', 'code', 'src'}:
                    raise ToolkitError('report destination overlaps protected source/configuration directories')
                if args.report.casefold() in {'agents.md', 'claude.md', 'gemini.md', 'problem_statement.md'}:
                    raise ToolkitError('report destination is protected')
                if args.report.startswith('.orchestrate/') and not args.report.startswith('.orchestrate/reports/'):
                    raise ToolkitError('report destination overlaps toolkit state')
                result = evaluation.evaluate(root, args.config, args.allow_exec, args.pass_env)
                target.parent.mkdir(parents=True, exist_ok=True)
                write_new(target, json_bytes(result))
                code = {'PASS': 0, 'FAIL': 1, 'UNKNOWN': 3}[result['overall']]
                print(json_bytes(result).decode('utf-8'), end='')
                return code
            elif args.command == 'workflow':
                if args.action == 'init':
                    result = workflow.init(root)
                elif args.action == 'status':
                    result = workflow.load(root)
                elif args.action == 'advance':
                    if not args.to or not args.evidence:
                        raise ToolkitError('advance requires --to and --evidence')
                    result = workflow.advance(root, args.to, args.evidence, args.approve_submit)
                else:
                    if not args.to or not args.reason:
                        raise ToolkitError('recover requires --to and --reason')
                    result = workflow.recover(root, args.to, args.reason)
            else:
                raise ToolkitError('unknown operation')
            code = 1 if args.command == 'doctor' and result['installation'] == 'FAIL' else 0
        print(json_bytes(result).decode('utf-8'), end='')
        return code
    except (ToolkitError, OSError, ValueError, TypeError, KeyError, RecursionError, csv.Error,
            subprocess.TimeoutExpired) as exc:
        # Do not echo arbitrary input/config/command content, which may contain secrets.
        print('ERROR: operation refused (' + type(exc).__name__ + '). ' +
              (str(exc) if isinstance(exc, ToolkitError) else 'Check configuration, paths and permissions.'), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
