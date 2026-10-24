"""Additive V4 command registration and dispatch for the existing public CLI."""

from pathlib import Path
from . import assessment, challenge, installer, interview, memory, mentor, records, release, scoring, security
from .common import ToolkitError

COMMANDS = {'analyze', 'assess', 'estimate', 'mentor', 'interview', 'memory', 'release-gate', 'security', 'restore'}


def register(commands):
    for name in sorted(COMMANDS):
        parser = commands.add_parser(name)
        parser.add_argument('--project', default='.')
        parser.add_argument('--report', help='new project-relative report; existing files are never replaced')
        parser.add_argument('--format', choices=['json', 'md'], default='json')
        if name == 'analyze':
            parser.add_argument('--source', action='append')
        elif name in ('assess', 'estimate', 'release-gate'):
            parser.add_argument('--config', required=True)
            if name == 'assess':
                parser.add_argument('--allow-exec', action='store_true')
                parser.add_argument('--pass-env', action='append', default=[])
        elif name == 'mentor':
            parser.add_argument('--evaluation')
            parser.add_argument('--design')
            parser.add_argument('--experiment')
        elif name == 'interview':
            parser.add_argument('action', choices=['prepare', 'check'])
            parser.add_argument('--code', action='append', default=[])
            parser.add_argument('--evaluation')
            parser.add_argument('--experiment')
            parser.add_argument('--answers')
            parser.add_argument('--claims')
        elif name == 'memory':
            parser.add_argument('action', choices=['create', 'decide', 'show', 'list', 'compare'])
            parser.add_argument('--id')
            parser.add_argument('--config')
            parser.add_argument('--first')
            parser.add_argument('--second')
        elif name == 'security':
            parser.add_argument('--file', action='append', required=True)
        elif name == 'restore':
            parser.add_argument('--backup', required=True)
            parser.add_argument('--scope', choices=['project', 'user'], default='project')
            parser.add_argument('--home', type=Path)
            parser.add_argument('--dry-run', action='store_true')
            parser.add_argument('--approve-restore', action='store_true')


def handle(root, args):
    if args.report:
        records.destination(root, args.report)  # Refuse bad/clobbering output before any approved operation.
    if args.command == 'analyze':
        result = challenge.analyze(root, args.source)
    elif args.command == 'assess':
        result = assessment.assess(root, args.config, args.allow_exec, args.pass_env)
    elif args.command == 'estimate':
        result = scoring.estimate(root, args.config)
    elif args.command == 'mentor':
        result = mentor.review(root, args.evaluation, args.design, args.experiment)
    elif args.command == 'interview':
        if args.action == 'prepare':
            result = interview.prepare(root, args.code, args.evaluation, args.experiment)
        elif not args.answers:
            raise ToolkitError('interview check requires --answers')
        else:
            result = interview.check(root, args.answers, args.claims)
    elif args.command == 'release-gate':
        result = release.gate(root, args.config)
    elif args.command == 'security':
        result = security.scan(root, args.file)
    elif args.command == 'restore':
        result = installer.restore(root, args.backup, args.scope, args.dry_run, args.approve_restore)
    elif args.command == 'memory':
        if args.action == 'list':
            result = memory.listing(root)
        elif args.action == 'create' and args.config:
            result = memory.create(root, args.config)
        elif args.action == 'show' and args.id:
            result = memory.history(root, args.id)
        elif args.action == 'decide' and args.id and args.config:
            result = memory.decide(root, args.id, args.config)
        elif args.action == 'compare' and args.first and args.second:
            result = memory.compare(root, args.first, args.second)
        else:
            raise ToolkitError('memory action needs its explicit ID/config or comparison pair')
    else:
        raise ToolkitError('unsupported V4 command')
    result.setdefault('overall', 'PASS')  # Operational success does not change recommendation/decision fields.
    print(records.output(root, result, args.report, args.format), end='')
    return {'PASS': 0, 'FAIL': 1, 'WARN': 3, 'UNKNOWN': 3}[result['overall']]
