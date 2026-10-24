# CLI reference

Run from a checkout with `python -m orchestrate_toolkit`, or install the package
and use `orchestrate-toolkit`. The community toolkit's `orchestrate` command is
separate and is not shadowed. Every command accepts `--help`.

## Installation lifecycle

```text
python -m orchestrate_toolkit install --agent codex --project ../entry --dry-run
python -m orchestrate_toolkit install --agent codex --project ../entry
python -m orchestrate_toolkit install --agent all --project ../entry
python -m orchestrate_toolkit doctor --project ../entry
python -m orchestrate_toolkit uninstall --agent codex --project ../entry --dry-run
python -m orchestrate_toolkit uninstall --agent all --project ../entry
```

Repeat --agent for selected agents. `all` must appear alone. Running the same
install again is idempotent. Unowned files and user edits are conflicts even if
replacement would be convenient. `--upgrade` updates only unmodified toolkit-owned
files and creates a backup under `.orchestrate/backups/`. No force-overwrite flag
exists. Uninstall removes unchanged owned files only and leaves shared files
needed by other agents. It retains the ownership ledger's audit history, backups,
workflow evidence and empty folders.

For optional user scope, only codex, claude, gemini and opencode are implemented:

```text
python -m orchestrate_toolkit install --agent codex --scope user --dry-run
python -m orchestrate_toolkit install --agent codex --scope user
python -m orchestrate_toolkit doctor --scope user
python -m orchestrate_toolkit uninstall --agent codex --scope user
```

`--home PATH` selects an existing home directory explicitly, useful for isolated
testing. It is invalid in project scope. Global rules for other agents are not
guessed; use project-local installation or manual reading.

## Validation and compatibility

```text
python -m orchestrate_toolkit validate
python -m orchestrate_toolkit compatibility --project ../entry
python tools/static_check.py
python tools/benchmark.py --out ../new-benchmark.json
```

Validate checks every canonical skill with the existing metadata/reference/CLI
validator. Doctor checks ownership integrity and reports executable/configuration
presence without launching an agent. Neither command tests live discovery.

## Evaluation

```text
python -m orchestrate_toolkit evaluate --project ../entry --config evaluation.json --report evaluation/report-001.json
python -m orchestrate_toolkit evaluate --project ../entry --config evaluation.json --report evaluation/report-002.json --allow-exec
```

Config paths and report paths are project-relative. Reports must be new and
outside protected source, starter and state paths. Config keys:

| Key | Purpose |
|---|---|
| contract | Path to the packaging companion's strict JSON contract |
| authority | Current human-selected specification path, recorded by hash |
| baseline / replay | CSV to compare with configured output, using exact schemas and IDs |
| checks | List of name, argv array, timeout (default 60, maximum 300), retries (default 0, maximum 2) |
| usage / run_id | JSONL records and optional final-run filter |
| prices | Mapping from model string to input/output USD per million tokens |
| requirements | Simple name==version requirements to check locally; other syntax UNKNOWN |
| estimate_text | UTF-8 text for a clearly labeled chars/4 token estimate |

Missing contract or withheld execution consent stays UNKNOWN. Commands are not
run by default. `--allow-exec` grants consent for configured local checks, not a
sandbox. `--pass-env NAME` explicitly forwards that variable; values never appear
in reports. Outputs/arguments are not echoed; reports include hashes, status,
classification, attempt counts and elapsed time. Cache pricing stays UNKNOWN in
this facade; use the existing usage-report script for cache-price support.

Baseline/replay movement is a failure to investigate, not automatically an
accuracy regression. Official scores always remain UNKNOWN. Current challenge
rules and hidden accuracy are not inferred from historical rubric text.

## Workflow

```text
python -m orchestrate_toolkit workflow init --project ../entry
python -m orchestrate_toolkit workflow status --project ../entry
python -m orchestrate_toolkit workflow advance --project ../entry --to ANALYZE --evidence notes.md
python -m orchestrate_toolkit workflow recover --project ../entry --to BUILD --reason "inspect the failed fixture"
```

States: DISCOVER, ANALYZE, PLAN, BUILD, TEST, EVALUATE, IMPROVE, VALIDATE, SUBMIT.
For TEST/EVALUATE/VALIDATE use a new PASS evaluation report as evidence. SUBMIT
needs the packaging companion's manifest and `--approve-submit`. That flag records
approval to hand off the verified local package; no remote action occurs.

## Exit codes and recovery

Most operations: 0 success, 1 failed validation/doctor, 2 invalid input or refused
operation. Evaluate additionally uses 3 for UNKNOWN. A source validator timeout
or inaccessible file is an error rather than a pass. The original checker exit
codes are unchanged.

If a process crashes, inspect operation.lock and the ledger before removing a
stale lock manually. Do not delete another running operation's lock. Interrupted
multi-file installs can leave unowned partial files; preserve them for inspection
and restore from a backup rather than adopting them blindly. Transactions roll
back caught errors; no claim of power-loss atomicity is made.
