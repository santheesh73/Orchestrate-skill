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
| Compliance trap (editing `AGENTS.md` or overwriting `CLAUDE.md`) | `hackerrank-orchestrate/SKILL.md` hard rule 1; `hackerrank-orchestrate/references/starter-contract.md` | Plus the `tool=` rule, checked by `hackerrank-orchestrate/scripts/check_log.py` |
| Prompt templates | `hackerrank-orchestrate/references/prompt-templates.md` | Adds an output-row pass |
| Winning approaches | `hackerrank-orchestrate/references/winning-approaches.md`; `hackerrank-orchestrate/references/archetypes/index.md` | Per-edition patterns split into archetype pages |
| Leaderboard readings | `hackerrank-orchestrate/references/rubric.md` §5 | Labeled INFERRED (secondhand) |
| Evaluation and anti-overfitting | `hackerrank-orchestrate/references/evaluation.md` | Its two contradictions are resolved; this file wins any conflict |
| Toolkit digest | `hackerrank-orchestrate/references/kit-repo.md`; `hackerrank-orchestrate/references/self-score.md` § Path B | Optional; pinned source inspected directly; command availability separated from behavioral verification |
| Toolkit judge prep | `hackerrank-orchestrate/references/interview.md` | Drill generated from your own code |
| Toolkit time budget | `hackerrank-orchestrate/references/loop-patterns.md` §7 | Same budget, plus `hackerrank-orchestrate/references/behind-schedule.md` |
| Hard rules | `hackerrank-orchestrate/SKILL.md` § Hard rules | One canonical copy; validator rejects restatements |
| Lessons from past editions | `hackerrank-orchestrate/references/archetypes/simulation-planning.md`; `hackerrank-orchestrate/references/interview.md` §1 | General lessons kept; personal results removed |
| Keeping the skill current | `hackerrank-orchestrate/references/edition-update.md`; `hackerrank-orchestrate/assets/editions/template.json` | Repeatable process instead of a dated plan |
| Self-score gate | `hackerrank-orchestrate/scripts/selfcheck.py` | One command instead of a toolkit dependency |

## 3. Added here, with no orchestrate-loop counterpart

| Addition | Failure it prevents |
|---|---|
| `hackerrank-orchestrate/scripts/` (10 checkers) and `tests/` (262 tests) | Rules that nobody can run; regressions in the checkers and optional companions |
| `hackerrank-orchestrate/assets/editions/` | A log checker that rejects another edition's format |
| `tools/validate_skill.py` | Structure and policy drift (dates in the trigger, restated rules, missing scripts) |
| `tools/package_skill.py` | A rejected upload, or dev files shipped inside the skill |
| `tools/footprint.py` | Silent growth of the always-loaded context |
| `tools/run_trigger_evals.py` and `evals/triggers.json` | Trigger regressions going unnoticed |
| `tests/test_cli_matrix.py` | The next crash on input nobody tried: every CLI against every hostile input class |
| `hackerrank-orchestrate/scripts/experiment.py` | A change-record verdict worked out by hand, two ways |
| `docs/AUDIT.md` and `tests/test_audit.py` | A capability that reads as working but was never made to fail (mutation-tested rows) |

## 4. Deliberately not ported

- Personal results, ranks and per-stage scores: personal data, not guidance.
- The full-stack build loop (section 8 of its loop page): a different HackerRank product, out of scope.
- The dated next-edition checklist: stale after one edition; replaced by `hackerrank-orchestrate/references/edition-update.md`.
- Copying the toolkit's skills into `.claude/skills/`: overlapping triggers would compete with this skill.
- Its text: the repository has no license, so ideas are restated in new wording and credited in the README.

## 5. Portability

The skill is one folder whose `SKILL.md` frontmatter holds only `name` and `description`, so each agent below reads it unchanged. Where it goes, and how sure we are, is in `docs/INSTALL.md`, which is the only place install folders are written down.

| Agent | Evidence (see `docs/INSTALL.md`) | Check here |
|---|---|---|
| Claude Code | VERIFIED: loaded and invoked from `.claude/skills/` in one run, not invoked for one near miss | `tools/package_skill.py --for claude` |
| Claude.ai | DOCS-READ: zip upload | `tools/package_skill.py` builds the zip; `tests/test_tools.py` checks its layout |
| OpenAI Codex, OpenCode, Google Antigravity, Cursor | DOCS-READ: `.agents/skills/` in the project; running the skill there is UNKNOWN | `tools/package_skill.py --for agents` |

| Guard | Failure it prevents |
|---|---|
| `tools/validate_skill.py`: `docs/INSTALL.md` names all six agents; no agent-specific install folder in the `SKILL.md` body | An agent silently dropped from the install guide; one agent's folder baked into the instructions every agent reads |
| `tests/test_tools.py` (`ProjectInstall`, `PortabilitySmoke`) | A layout that installs differently from the other, or an installed copy whose scripts need the repository, the network or the caller's working directory |
| `evals/triggers.json` cases phrased by Codex, Cursor, OpenCode and Antigravity users | A trigger that only fires for people who say "Claude" |
| Hard rule 1 in `hackerrank-orchestrate/SKILL.md` | Editing the starter's `AGENTS.md`, the contract every agent's log is graded against |

## 6. Optional companions

The original rules and ten checker scripts are preserved. The main skill gains
an approved I/O/recovery paragraph; current content hashes are checked against `integrations/upstreams.json`.

| Companion | Added evidence and checks |
|---|---|
| hackerrank-orchestrate-design | Adaptable design contract, typed seam, failure and evaluation template |
| hackerrank-orchestrate-package | Exact archive allowlist, required files, CSV validation, hash manifest and atomic new bundle |
| hackerrank-orchestrate-practice | Source-grounded rehearsal and authentic transcript review |
| hackerrank-orchestrate-toolkit | Pinned optional CLI integration, applicability and estimate boundaries |

`tests/test_submission_package.py` covers failure controls and distinct synthetic
schemas. `tests/test_addons.py` checks preservation, standalone installed use,
refusal to overwrite and rollback. `tools/ci_check.py` validates copied packages
on each configured platform; `tools/package_addons.py` leaves the original skill
untouched. See `docs/integrations/community-toolkit.md` for scope and limits.

## 7. Universal offline facade

`orchestrate_toolkit/` adds documented adapter generation, owned install/uninstall,
doctor, checkpoints and structured evaluation without replacing the original
scripts. `tests/test_universal.py` exercises every adapter and trust boundary with
synthetic filesystem/subprocess scenarios. `tools/wheel_smoke.py` exercises a
temporary wheel installation outside the checkout, including the console command.
`tools/static_check.py` covers new source syntax and prohibited shell invocation.
See `docs/COMPATIBILITY.md`, `docs/CLI.md` and `docs/UNIVERSAL-AUDIT-PLAN.md`.

## 8. Comparative audit evidence

`benchmarks/comparison/` runs identical synthetic artifacts through both reviewed
repositories and separates unsupported policies from common-interface error
rates. `tests/test_v2_evidence.py` covers healthy/injected/metamorphic controls,
deliberately broken checkers, unknown coverage, the opt-in decision-ID policy,
evidence-kind separation and shared fixture fingerprints. `audit-selftest`
reuses contract/replay validators without executing participant code.
See `docs/COMPETITIVE_BASELINE.md` for measurements and their limits.

## 9. Behavioral and source-bound evidence

`hackerrank-orchestrate-evidence` adds a self-contained offline grader and a
checkout entrypoint in `tools/evaluate_behavior.py`. `evals/behavior/` has eight
public synthetic cases with expected answers separated from prepared workspaces.
The public selftest exercises healthy outputs, invalid outputs and starter changes.
`tests/test_behavior_evidence.py` tests broken graders, paired-comparison fairness,
missing traces, stale citations, test-result bindings and the complete fictional
practice-to-package route. CI runs no live coding agent. Citation integrity and
trace consistency do not establish semantic truth or authenticated invocation.
See `docs/BEHAVIOR_EVALUATION.md`, `docs/LIVE_VERIFICATION.md` and
`docs/HACKATHON_PRACTICE.md`.
