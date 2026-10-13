# Behind schedule

Failure it prevents: cutting a whole gate (usually the usage report, the fresh-clone run or the interview drill) when time runs short.

Skip depth inside a gate, never the gate. Every cut below keeps all four artifacts valid. Times are hours before the deadline.

## T-6h: stop adding features
1. Freeze the architecture. No new tools, stages or models. Only fix bugs and contract misses.
2. Run `scripts/selfcheck.py` now, so the remaining hours go to its FAIL rows first.
3. Cut: further accuracy work on rows inside the noise floor, extra archetype guards you have not started, diagrams.
4. Keep: one full-dataset run from the cache, the output-row pass on boundary calls, `CONSTANTS.md` complete.

## T-3h: freeze the code
1. Last code change, then one full run that produces the final `output.csv` and the usage log.
2. Generate `evaluation/usage_report.md` from that exact run.
3. Fresh clone, install from the README, run once. Fix only what breaks the run.
4. Cut: refactors, renames, new tests beyond one per fixed defect, README polish beyond setup and run.
5. Start the interview drill (`scripts/interview_drill.py`) while the run finishes.

## T-1h: package and verify
1. `scripts/selfcheck.py` once more: log, output, usage report must be PASS.
2. Re-derive every number you will cite (`scripts/claim_audit.py`).
3. Confirm no secrets, no organizer-only files, `AGENTS.md` and `CLAUDE.md` untouched, zip contains the required files.
4. Submit. Do not make a last-minute change you cannot re-run end to end.

## Freeze first, verify last
- Freeze first: architecture, then prompts, then constants, then code.
- Verify last: the submitted zip, `output.csv` and `log.txt` agree with each other; the usage report describes the run that produced the submitted output.
- After submitting, sleep before the interview if the window allows.
