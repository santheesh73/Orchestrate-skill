# Self-score (gate 7)

Never skipped. It works with or without the community toolkit.

## Path A: bundled scripts plus manual checklist (always available)

One command runs the automated part. Write a `selfcheck.json` once (the format is in `scripts/selfcheck.py --help`), then:

```
python scripts/selfcheck.py selfcheck.json
```

It runs, and prints one row each for: the starter files (`AGENTS.md` unchanged since kickoff, hard rule 1), the log (`check_log.py`), the output contract (`preflight.py`), the usage report's existence and content, constants missing from `CONSTANTS.md` (`interview_drill.py`), code literals copied from the dataset (`corpus_literals.py`), and numbers in docs versus the live repo (`claim_audit.py`). A section you did not configure, or one that examined nothing, prints UNKNOWN, never PASS. Fix every FAIL before moving on; read every WARN.

Two checks are not in selfcheck because they need two runs. Do them by hand:
- `scripts/rerun_diff.py` on two offline runs from the cache: zero changed rows.
- Once, against a cold re-derivation, to record the noise floor.

Then score each artifact against `rubric.md` honestly, one line each, labeled VERIFIED or INFERRED:

**Code (30)**
- [ ] One named, findable agent loop with explicit cap, fallback and validated output
- [ ] Prompts and tool descriptions in named files; tools testable without the model
- [ ] Deterministic core separated from the model layer; model never writes a final value
- [ ] Rationale in docstrings and beside constants; README is setup and run only
- [ ] Pinned dependencies, seeded or deterministic sampling, secrets from env vars
- [ ] Runs from a fresh clone with only the README; tests pass, each file alone
- [ ] No corpus literals or hardcoded labels (`corpus_literals.py`)

**Output CSV (30)**
- [ ] Preflight clean; distribution not collapsed onto one value
- [ ] Boundary definitions in the prompt; justifications specific and grounded
- [ ] Adversarial rows checked separately

**Interview (30)**
- [ ] Drill answered against the code; one row traced; rejections with numbers ready

**Transcript (10)**
- [ ] Plan stated before code; architecture chosen by you; drafts rejected with reasons; verification visible; log entries valid

Name the weakest artifact and spend the next block of time there.

## Path B: community toolkit (optional)

If the community toolkit is installed, optionally run its gates (`python -m orchestrate_kit evaluate .`, `python -m orchestrate_kit mentor "<proposal>" --repo .`, and `python -m orchestrate_kit release .` at freeze). See `kit-repo.md` for the inspected source and applicability. Inspect audits run/skipped, not just a summary. Its scores are heuristics, not HackerRank predictions. If absent, Path A is the complete gate. Existing evaluation policy governs conflicts; a demonstrated contract defect must be fixed even when it affects one row.
