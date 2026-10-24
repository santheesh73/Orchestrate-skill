---
name: hackerrank-orchestrate
description: Playbook for competing in HackerRank Orchestrate, the timed AI-agent hackathon graded on code zip, output CSV, AI judge interview and chat transcript. Covers the per-artifact scoring breakdown, the first-15-minutes starter-repo contract check (AGENTS.md, log.txt tool= rule, usage_report.md), agent architecture by problem type, the change-record iteration loop, output-CSV and interview prep, paste-ready prompts for the user's coding agent, and bundled checker scripts. Use when the user is preparing for, competing in, or reviewing a HackerRank Orchestrate submission, pastes an Orchestrate problem_statement.md or AGENTS.md, or asks for a kickoff, iteration or freeze prompt for that hackathon. Do not use for general prompt writing, other hackathons, or ordinary coding-agent work that has no Orchestrate context.
---

# HackerRank Orchestrate

A playbook for one event: HackerRank Orchestrate. Each edition ships a fresh starter repo (`AGENTS.md`, `problem_statement.md`, `dataset/`, mandatory `log.txt` logging) and a 24-hour window. The submission is graded on four artifacts, and balance across all four beats a peak in one.

## Working style

- Terse and directive. Deliver complete, paste-ready output.
- Default role: **draft prompts; the user's coding agent builds.** The user drives that agent (Claude Code, Codex, Cursor, OpenCode, Antigravity or another harness). Produce submission code directly only on request; building scaffolding when a prompt was wanted is a common mistake.
- A pasted agent report gets checked against real artifacts (files, hashes, live test counts, script output) before you reply with the following prompt.
- Do not make up a score, percentage, rank estimate or test count. Label every figure VERIFIED, MEASURED, INFERRED or UNKNOWN.
- The live challenge page and this edition's `AGENTS.md` and `problem_statement.md` override everything in this skill.

## What to read, when

| Moment | Read |
|---|---|
| Before the event, or the user asks how it is scored | `references/rubric.md` |
| The starter repo drops (first 15 minutes) | `references/starter-contract.md` and `scripts/contract_extract.py`; run `scripts/check_log.py` once logging starts |
| Choosing an architecture once the problem is known | `references/archetypes/index.md` (pick the closest page; say so when none fits) and `references/winning-approaches.md` |
| Building and iterating | `references/loop-patterns.md` and `references/evaluation.md` |
| Writing a prompt for the coding agent | `references/prompt-templates.md` |
| Improving output rows and justifications | `references/output-csv.md` |
| Preparing for the AI judge interview | `references/interview.md`, then run `scripts/interview_drill.py` |
| Self-scoring, with or without the community toolkit | `references/self-score.md` and `scripts/selfcheck.py` |
| Behind schedule | `references/behind-schedule.md` |
| An edition has ended; updating this skill | `references/edition-update.md` |
| V4 CLI, memory, mentor or release gates | `references/v4-workflow.md` |

Templates live in `assets/`: `change_record.md`, `decision_log.md`, `CONSTANTS.md`, `usage_log_schema.md`.

## Inputs, outputs and recovery

Inputs: current spec, starter rules, artifacts and requested mode. Output: a checked plan, prompt or evidence report. Missing evidence stays UNKNOWN; request blocking inputs. Validate with the relevant bundled checks before claiming completion.

## Core principle

**Model describes, code decides.** The model reads messages, documents and images and returns a typed record of observations. Plain, unit-tested code turns that record into every number, label and plan. This makes the run repeatable from a cache, auditable per row, and injection-resistant by structure. State the boundary: "deterministic given the cached model record", never "deterministic" alone.

## Hard rules (canonical copy; other files link here)

1. **Leave the starter's agent-instruction files intact.** `AGENTS.md` is the contract that makes `log.txt` logging mandatory; never edit it. When `CLAUDE.md` is just `@AGENTS.md`, keep that line: add text under it, or put strategy in the opening message.
2. **Obey the starter contract literally.** Exact output columns and order, one row per input id, allowed values, required files (for example `evaluation/usage_report.md`), and a correct `tool=` line in every log entry. Read the contract fresh each edition; it changes.
3. **Samples motivate or falsify; the domain justifies.** Sample rows are examples, not labels. Never add a rule, constant or threshold whose only justification is that it improves sample accuracy, and never iterate until one sample number matches.
4. **One labeled row is noise.** Revert a change when it regresses a label-free check, or when it regresses two or more labeled rows that its stated reasoning does not explain. Never accept or reject on a one-row difference. The full resolution table is in `references/evaluation.md`.
5. **Choose the grouping keys and the per-group statistic before any detector exists.** Later fixes cannot recover what a bad grouping discarded.
6. **No decision may hinge on whether a free-text field from the model is empty or not.** Branch on booleans and enums.
7. **Every non-trivial change gets a change record** (`assets/change_record.md`): ceiling first, then claim, metric, baseline, blast radius, counterfactual, verdict.
8. **Rationale lives in source.** The code grader reads source only. Put design reasons in module docstrings and comments beside constants; keep the README for setup and run instructions.
9. **Every constant has a row in `CONSTANTS.md` saying where it came from** (MEASURED / SPEC / STANDARD / BOUND / JUDGEMENT). A value nobody tuned is not described as "chosen after evaluation".
10. **Prove counterfactuals.** Switch a component off and show that its effect goes away. Distrust a perfect "nothing changed" from a harness nobody has checked.
11. **One bad row never kills the run.** Validate, retry once, then write an honest escalation or safe-default row. Never write a partial output file.
12. **Self-score is never skipped; it degrades gracefully.** With the community toolkit installed, run it. Without it, run `scripts/selfcheck.py` and the manual checklist in `references/self-score.md`. A skipped check is UNKNOWN, never a pass.
13. **Rehearse the interview before deadline pressure.** Drill from your own code, and never say anything about the implementation you have not checked against it.
14. **Say where each guarantee ends, and raise your limitations yourself before the judge does.**

## Bundled scripts

Standard-library Python 3.9+, no installs. Each takes paths and schemas as arguments and embeds no dataset. They check the work; they are not part of the submission (the participant must be its author). Run with `--help` for options.

| Script | Checks |
|---|---|
| `scripts/selfcheck.py selfcheck.json` | Gate 7 in one command: runs the checks below from one config; skipped means UNKNOWN |
| `scripts/contract_extract.py STARTER_DIR [--diff OLD NEW]` | MUST / MUST NOT / files / columns / allowed values / order lines with file:line (heuristic) |
| `scripts/check_log.py log.txt --expect-tool "HARNESS" [--profile NAME]` | One valid `tool=` line per entry, prompt block present, no secrets, append-only; formats in `assets/editions/` |
| `scripts/preflight.py output.csv --template … --inputs … --id-col …` | Exact header and order, one row per input id, no duplicates, enums, blanks |
| `scripts/rerun_diff.py run_a.csv run_b.csv --id-col …` | Row and column churn between two runs; the noise floor |
| `scripts/experiment.py start NAME …`, then `finish NAME` | One change record: re-run, full-set diff, labeled rows better and worse, the resolution-table verdict |
| `scripts/usage_report.py usage.jsonl --price MODEL=IN:OUT` | Builds `evaluation/usage_report.md` from a per-call token log |
| `scripts/interview_drill.py code/ --constants CONSTANTS.md` | Questions from your own constants, thresholds and orderings, with file:line |
| `scripts/corpus_literals.py --data … --code code/ --spec …` | Code literals copied from the dataset (sample coupling) |
| `scripts/claim_audit.py README.md CONSTANTS.md --repo .` | Numbers in docs versus the live repo (hints, not proof) |

Keep personal results and dataset-specific notes out of this skill; put them in project memory.
