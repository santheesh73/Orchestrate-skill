---
name: hackerrank-orchestrate
description: Playbook for competing in HackerRank Orchestrate, the timed AI-agent hackathon graded on code zip, output CSV, AI judge interview and chat transcript. Covers the per-artifact scoring breakdown, the first-15-minutes starter-repo contract check (AGENTS.md, log.txt tool= rule, usage_report.md), agent architecture by problem type, the change-record iteration loop, output-CSV and interview prep, paste-ready Claude Code prompts for the event, and bundled checker scripts. Use when the user is preparing for, competing in, or reviewing a HackerRank Orchestrate submission, pastes an Orchestrate problem_statement.md or AGENTS.md, or asks for a kickoff, iteration or freeze prompt for that hackathon. Do not use for general prompt writing, other hackathons, or ordinary Claude Code work that has no Orchestrate context.
---

# HackerRank Orchestrate

A playbook for one event: HackerRank Orchestrate. Each edition ships a fresh starter repo (`AGENTS.md`, `problem_statement.md`, `dataset/`, mandatory `log.txt` logging) and a 24-hour window. The submission is graded on four artifacts, and balance across all four beats a peak in one.

## Working style

- Terse and directive. Deliver complete, paste-ready output.
- Default role: **write the prompt for Claude Code**; the user runs Claude Code to build. Write submission code yourself only when asked. Over-building scaffold instead of giving the prompt is a known failure.
- When the user pastes a Claude Code report, check its claims against real artifacts (files, hashes, live test counts, script output), then answer with the next prompt.
- Never fabricate scores, percentages, rank odds or test counts. Label every figure VERIFIED, MEASURED, INFERRED or UNKNOWN.
- The live challenge page and this edition's `AGENTS.md` and `problem_statement.md` override everything in this skill.

## What to read, when

| Moment | Read |
|---|---|
| Before the event, or the user asks how it is scored | `references/rubric.md` |
| The starter repo drops (first 15 minutes) | `references/starter-contract.md`, then run `scripts/check_log.py` once logging starts |
| Choosing an architecture once the problem is known | `references/archetypes/index.md` (pick the closest page; say so when none fits) and `references/winning-approaches.md` |
| Building and iterating | `references/loop-patterns.md` and `references/evaluation.md` |
| Writing a Claude Code prompt | `references/prompt-templates.md` |
| Improving output rows and justifications | `references/output-csv.md` |
| Preparing for the AI judge interview | `references/interview.md`, then run `scripts/interview_drill.py` |
| Self-scoring, with or without the community toolkit | `references/self-score.md` |

Templates live in `assets/`: `change_record.md`, `decision_log.md`, `CONSTANTS.md`, `usage_log_schema.md`.

## Core principle

**Model describes, code decides.** The model reads messages, documents and images and returns a typed record of observations. Plain, unit-tested code turns that record into every number, label and plan. This makes the run repeatable from a cache, auditable per row, and injection-resistant by structure. State the boundary: "deterministic given the cached model record", never "deterministic" alone.

## Hard rules (canonical copy; other files link here)

1. **Do not overwrite the starter `CLAUDE.md`.** It is `@AGENTS.md`, which drives mandatory `log.txt` logging. Append below it, or send strategy as the first message.
2. **Obey the starter contract literally.** Exact output columns and order, one row per input id, allowed values, required files (for example `evaluation/usage_report.md`), and a correct `tool=` line in every log entry. Read the contract fresh each edition; it changes.
3. **Samples motivate or falsify; the domain justifies.** Sample rows are examples, not labels. Never add a rule, constant or threshold whose only justification is that it improves sample accuracy, and never iterate until one sample number matches.
4. **One labeled row is noise.** Revert a change when it regresses a label-free check, or when it regresses two or more labeled rows that its stated reasoning does not explain. Never accept or reject on a one-row difference. The full resolution table is in `references/evaluation.md`.
5. **Decide grouping keys and statistics before writing a detector.** Patches inherit whatever the grouping already threw away.
6. **Never gate a decision on the truthiness of a model-written free-text field.** Gate on booleans and enums only.
7. **Every non-trivial change gets a change record** (`assets/change_record.md`): ceiling first, then claim, metric, baseline, blast radius, counterfactual, verdict.
8. **Rationale lives in source.** The code grader reads source only. Put design reasons in module docstrings and comments beside constants; keep the README for setup and run instructions.
9. **Keep `CONSTANTS.md` with a provenance column** (MEASURED / SPEC / STANDARD / BOUND / JUDGEMENT). Never call an untuned value "chosen after evaluation".
10. **Prove counterfactuals.** Disable a component and show its effect stops. A clean "0 rows changed" from an unverified harness is suspect.
11. **One bad row never kills the run.** Validate, retry once, then write an honest escalation or safe-default row. Never write a partial output file.
12. **Self-score is never skipped; it degrades gracefully.** With the community toolkit installed, run it. Without it, run the bundled scripts and the manual checklist in `references/self-score.md`.
13. **Rehearse the interview before deadline pressure.** Drill from your own code, and never say anything about the implementation you have not checked against it.
14. **State the boundary of every guarantee and name limitations before the judge asks.**

## Bundled scripts

Standard-library Python 3.9+, no installs. Each takes paths and schemas as arguments and embeds no dataset. They check the work; they are not part of the submission (the participant must be its author). Run with `--help` for options.

| Script | Checks |
|---|---|
| `scripts/check_log.py log.txt --expect-tool "Claude Code"` | Every entry has one valid `tool=` line, verbatim prompt block present, no secrets, append-only timestamps |
| `scripts/preflight.py output.csv --template dataset/output.csv --inputs dataset/requests.csv --id-col request_id` | Exact header and order, one row per input id, no duplicates, enums, blanks |
| `scripts/rerun_diff.py run_a.csv run_b.csv --id-col request_id` | Row and column churn between two runs; the noise floor |
| `scripts/usage_report.py usage.jsonl --price MODEL=IN:OUT` | Builds `evaluation/usage_report.md` from a per-call token log |
| `scripts/interview_drill.py code/ --constants CONSTANTS.md` | Question bank from your own constants, thresholds and orderings, each with file:line |

## After each edition

Update `references/archetypes/` with the new problem shape and `references/rubric.md` if the weights changed. Keep personal results and dataset-specific notes out of this skill; put them in project memory.
