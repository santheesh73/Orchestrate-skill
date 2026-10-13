# Coverage matrix

Failure it prevents: a gap nobody notices. Either a scored criterion has no guidance or check in the skill, or something useful in the earlier orchestrate-loop skill was dropped without a decision. `tests/test_tools.py` checks that every path below exists and that every row is present.

Paths are relative to the repository root. "§" names a section heading in that file. Scripts check a participant's own work; they are not part of a submission.

## 1. Rubric sub-criteria

Weights are from the May 2026 post-mortem (VERIFIED; see `hackerrank-orchestrate/references/rubric.md` §2).

| Artifact | Sub-criterion | Guidance | Check or template |
|---|---|---|---|
| Code zip | Agent architecture (30%) | `hackerrank-orchestrate/references/loop-patterns.md` §1; `hackerrank-orchestrate/references/archetypes/index.md` | `hackerrank-orchestrate/references/prompt-templates.md` §1 (kickoff) |
| Code zip | Prompt and tool craft (30%) | `hackerrank-orchestrate/references/loop-patterns.md` §1 (tool design); `hackerrank-orchestrate/references/winning-approaches.md` §2 (typed seam) | `hackerrank-orchestrate/scripts/interview_drill.py` (named constants with file:line) |
| Code zip | Agent robustness (25%) | `hackerrank-orchestrate/references/loop-patterns.md` §6; archetype pages § Guards that fit | `hackerrank-orchestrate/scripts/preflight.py`, `hackerrank-orchestrate/scripts/rerun_diff.py` |
| Code zip | Engineering rigor (15%) | `hackerrank-orchestrate/references/evaluation.md` §6 (merge gates) | `hackerrank-orchestrate/scripts/corpus_literals.py`, `hackerrank-orchestrate/scripts/claim_audit.py`, `hackerrank-orchestrate/assets/CONSTANTS.md` |
| Output CSV | Per-row accuracy | `hackerrank-orchestrate/references/output-csv.md` §2 and §3; `hackerrank-orchestrate/references/evaluation.md` §1 to §5 | `hackerrank-orchestrate/scripts/preflight.py`; `hackerrank-orchestrate/references/prompt-templates.md` §4 |
| Output CSV | One safety score for the submission | `hackerrank-orchestrate/references/output-csv.md` §4; `hackerrank-orchestrate/references/archetypes/adversarial-routing.md` | `hackerrank-orchestrate/scripts/preflight.py` (collapsed distribution) |
| Interview | Technical depth and ownership (40%) | `hackerrank-orchestrate/references/interview.md` §1 and §2 | `hackerrank-orchestrate/scripts/interview_drill.py` |
| Interview | Problem understanding and judgment (25%) | `hackerrank-orchestrate/references/interview.md` §3; `hackerrank-orchestrate/assets/decision_log.md` | `hackerrank-orchestrate/assets/change_record.md` |
| Interview | Communication clarity (20%) | `hackerrank-orchestrate/references/interview.md` §3 (answer shape) | `hackerrank-orchestrate/references/interview.md` §5 |
| Interview | Honesty and self-awareness (15%) | `hackerrank-orchestrate/references/interview.md` §4 | `hackerrank-orchestrate/scripts/claim_audit.py` |
| Transcript | Direction and architecture ownership (35%) | `hackerrank-orchestrate/references/loop-patterns.md` §2 | `hackerrank-orchestrate/assets/decision_log.md` |
| Transcript | Technical specificity and constraint (25%) | `hackerrank-orchestrate/references/prompt-templates.md` §1; `hackerrank-orchestrate/references/starter-contract.md` | `hackerrank-orchestrate/scripts/contract_extract.py` |
| Transcript | Iteration and verification (25%) | `hackerrank-orchestrate/references/loop-patterns.md` §3 and §5 | `hackerrank-orchestrate/assets/change_record.md`; `hackerrank-orchestrate/references/prompt-templates.md` §2 |
| Transcript | Safety, edge case and quality awareness (15%) | `hackerrank-orchestrate/references/winning-approaches.md` §3 (threat model, failure modes) | `hackerrank-orchestrate/scripts/check_log.py` (log compliance and secrets) |
| All four | Gate 7, self-score | `hackerrank-orchestrate/references/self-score.md` | `hackerrank-orchestrate/scripts/selfcheck.py` |

## 2. orchestrate-loop capabilities

| orchestrate-loop capability | Where it lives here | What changed |
|---|---|---|
| Six loops: agent loop | `hackerrank-orchestrate/references/loop-patterns.md` §1 | Framework loops accepted; the May winner's `create_agent` is VERIFIED in its code |
| Six loops: plan, build, review | `hackerrank-orchestrate/references/loop-patterns.md` §2 | Adds the who-decided log |
| Six loops: iteration with change record | `hackerrank-orchestrate/references/loop-patterns.md` §3; `hackerrank-orchestrate/assets/change_record.md` | Verdicts follow the resolution table in `hackerrank-orchestrate/references/evaluation.md` §4 |
| Six loops: prompt relay | `hackerrank-orchestrate/references/loop-patterns.md` §4 | Same idea |
| Six loops: verify before trust | `hackerrank-orchestrate/references/loop-patterns.md` §5 | Backed by runnable scripts instead of prose only |
| Six loops: per-row safety | `hackerrank-orchestrate/references/loop-patterns.md` §6 | Adds ABORT / DEGRADE / FAIL ROW dispositions |
| Phase gates (outer loop) | `hackerrank-orchestrate/references/loop-patterns.md` §7; `hackerrank-orchestrate/references/behind-schedule.md` | Adds what to cut when late |
| Rubric context | `hackerrank-orchestrate/references/rubric.md` | Every figure labeled VERIFIED or INFERRED |
| Compliance trap (overwriting `CLAUDE.md`) | `hackerrank-orchestrate/SKILL.md` hard rule 1; `hackerrank-orchestrate/references/starter-contract.md` | Plus the `tool=` rule, checked by `hackerrank-orchestrate/scripts/check_log.py` |
| Prompt templates | `hackerrank-orchestrate/references/prompt-templates.md` | Adds an output-row pass |
| Winning approaches | `hackerrank-orchestrate/references/winning-approaches.md`; `hackerrank-orchestrate/references/archetypes/index.md` | Per-edition patterns split into archetype pages |
| Leaderboard readings | `hackerrank-orchestrate/references/rubric.md` §5 | Labeled INFERRED (secondhand) |
| Evaluation and anti-overfitting | `hackerrank-orchestrate/references/evaluation.md` | Its two contradictions are resolved; this file wins any conflict |
| Toolkit digest | `hackerrank-orchestrate/references/kit-repo.md`; `hackerrank-orchestrate/references/self-score.md` § Path B | Optional; never a dependency; labeled secondhand |
| Toolkit judge prep | `hackerrank-orchestrate/references/interview.md` | Drill generated from your own code |
| Toolkit time budget | `hackerrank-orchestrate/references/loop-patterns.md` §7 | Same budget, plus `hackerrank-orchestrate/references/behind-schedule.md` |
| Hard rules | `hackerrank-orchestrate/SKILL.md` § Hard rules | One canonical copy; validator rejects restatements |
| Lessons from past editions | `hackerrank-orchestrate/references/archetypes/simulation-planning.md`; `hackerrank-orchestrate/references/interview.md` §1 | General lessons kept; personal results removed |
| Keeping the skill current | `hackerrank-orchestrate/references/edition-update.md`; `hackerrank-orchestrate/assets/editions/template.json` | Repeatable process instead of a dated plan |
| Self-score gate | `hackerrank-orchestrate/scripts/selfcheck.py` | One command instead of a toolkit dependency |

## 3. Added here, with no orchestrate-loop counterpart

| Addition | Failure it prevents |
|---|---|
| `hackerrank-orchestrate/scripts/` (9 checkers) and `tests/` (119 tests) | Rules that nobody can run; regressions in the checkers |
| `hackerrank-orchestrate/assets/editions/` | A log checker that rejects another edition's format |
| `tools/validate_skill.py` | Structure and policy drift (dates in the trigger, restated rules, missing scripts) |
| `tools/package_skill.py` | A rejected upload, or dev files shipped inside the skill |
| `tools/footprint.py` | Silent growth of the always-loaded context |
| `tools/run_trigger_evals.py` and `evals/triggers.json` | Trigger regressions going unnoticed |

## 4. Deliberately not ported

- Personal results, ranks and per-stage scores: personal data, not guidance.
- The full-stack build loop (section 8 of its loop page): a different HackerRank product, out of scope.
- The dated next-edition checklist: stale after one edition; replaced by `hackerrank-orchestrate/references/edition-update.md`.
- Copying the toolkit's skills into `.claude/skills/`: overlapping triggers would compete with this skill.
- Its text: the repository has no license, so ideas are restated in new wording and credited in the README.
