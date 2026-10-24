# Troubleshooting

## UNKNOWN is blocking a gate

Inspect checks and blockers in the JSON report. Missing checks, unsupported inputs,
unreviewed interpretations, stale sources or absent reproduction/manual evidence
must be resolved rather than relabeled. Citation-only and heuristic mentor reports
intentionally keep semantic questions UNKNOWN. They cannot replace participant
evaluation evidence. Exit 3 means WARN/UNKNOWN, not success.

## A report or demo directory already exists

Choose a new report filename or a new demo workspace. V4 report generation and
experiment creation do not overwrite previous evidence. Do not delete old records
just to make a command pass. Rerun measurements against the intended current files.

## Installation reports an unowned or modified file

Review the dry-run and preserve local edits. The installer does not force overwrite.
Use --upgrade only for unchanged owned files. Preview a matching V4 backup restore
with restore --backup ID --dry-run; applying it needs --approve-restore. Old backups
without restore.json need manual recovery. Do not modify the ownership ledger to
turn an unrelated file into toolkit-owned content.

## A checkpoint will not advance

Check workflow status, stage order, source/policy hashes, required files and evidence.
Three gate failures require explicit recovery, bounded to three recoveries. A V4
policy cannot be silently added to an existing legacy checkpoint. Preserve the
old checkpoint and start a reviewed fresh project/run when changing policies.
SUBMIT also requires the latest successful validation and explicit local approval.

## Windows blocks the generated console launcher

The local host has returned WinError 4551 for a generated console executable.
Do not disable or bypass Application Control. From a permitted source checkout,
the standard Python module interface is the supported alternative:
`python -m orchestrate_toolkit --help`. Whether an installed wheel's console
launcher can execute remains an environment-specific check. Report its actual
status separately from module, package and hosted-CI validation.

## A coding assistant does not load the skill

Installing files or finding an executable does not establish activation. Follow
the exact route in [compatibility evidence](COMPATIBILITY.md), identify the actual
file read in the runtime's genuine export, and test an unrelated request in a
fresh session. Current universal-adapter live verification remains UNKNOWN.

## A benchmark cannot execute the reference repository

Use the own-only benchmark and source comparison without claiming reference
runtime results. External code execution needs separate authorization and reviewed
isolation. Do not repackage an automatically rejected action as an indirect call.
The current V4 limitation is recorded in [benchmark scope](V4_BENCHMARK.md).
