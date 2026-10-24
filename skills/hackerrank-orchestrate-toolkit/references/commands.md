# Community toolkit bridge

Source: [NITISH-R-G/hackerrank-orchestrate-skills](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills), MIT, inspected revision `ccb175f8717f67fd084c57d853076f0b95636980` on 2026-10-24. Commands below were checked against its parser; only help and selftest were behaviorally exercised during the comparison. No toolkit source is bundled here.

## Optional installation

Use a dedicated Python 3.10+ virtual environment. The portable core skill still needs only standard-library Python 3.9+.

```text
python -m venv .venv-orchestrate-kit
```

Use that environment's Python executable (POSIX: `.venv-orchestrate-kit/bin/python`; Windows: `.venv-orchestrate-kit/Scripts/python.exe`) in place of PYTHON below:

```text
PYTHON -m pip install "git+https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git@ccb175f8717f67fd084c57d853076f0b95636980"
PYTHON -m orchestrate_kit --help
PYTHON -m orchestrate_kit selftest
```

This installs the CLI, not the upstream skill folders. Installation needs network access; runtime has no mandatory third-party dependencies. Use a new environment rather than replacing project packages.

## Commands

```text
python -m orchestrate_kit evaluate <project>
python -m orchestrate_kit mentor "<proposal>" --repo <project>
python -m orchestrate_kit score --repo <project> --no-history --python <project-python>
python -m orchestrate_kit transcript analyze <transcript>
python -m orchestrate_kit interview --persona skeptic --difficulty standard --save <new-result.json>
python -m orchestrate_kit release <project>
```

Check each command's help before using optional flags. Select a new result path so an existing rehearsal is preserved. Score can execute target-project checks. It does not predict the hidden grader.

For project-local engineering memory, place the global argument before the command:

```text
python -m orchestrate_kit --memory <project-memory.json> memory list
python -m orchestrate_kit --memory <project-memory.json> memory why-not "<idea>"
```

Seed only a new memory file when the user wants upstream examples. Label imported records as historical examples; do not describe their measurements as your own.

## Applicability and conflicts

The inspected Orchestrate evaluator detects `dataset/messages.csv` plus a problem statement and embeds message-router columns, enums and evidence rules. It reads `dataset/output.csv`; another edition or root output path needs an appropriate plugin or independent contract validation. Run the original skill's configurable preflight and selfcheck regardless of a generic toolkit verdict.

The toolkit's experiment command tracks heuristic score changes. The original skill's experiment script tracks actual output differences. A heuristic gain cannot override a contract violation, measured regression or missing evaluation.

The upstream phase skills contain sample-regression rules, harness-specific goal commands and references to unbundled skills. They are not installed by this bridge. Retain the participant's established evaluation policy and current starter contract.

The upstream submission packager returned READY for empty input and missing required usage evidence in synthetic probes. Use the separate hardened packaging companion and current contract instead.
