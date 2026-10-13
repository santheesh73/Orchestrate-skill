# The starter contract: the first 15 minutes

Every edition ships a new starter repo, and the contract in it changes. Points are lost to contract misses that no amount of model quality recovers. Do this before any design work.

## Checklist

1. **Read `AGENTS.md`, `problem_statement.md` and `README.md` in full.** Do not skim from a previous edition's memory.
2. **Leave `AGENTS.md` unedited, and confirm `CLAUDE.md` (if present) is just `@AGENTS.md`.** Add strategy below that import or as the first message. Run `scripts/selfcheck.py` once with a `starter` section: it prints the sha256 of `AGENTS.md` to record, and every later run fails if the file changed (hard rule 1).
3. **Extract every MUST into one list**, with the section it came from. `scripts/contract_extract.py STARTER_DIR` drafts it with file:line; confirm every line against the files:
   - output file name and location (for example root-level `output.csv`, not `dataset/output.csv`)
   - exact columns and order, allowed values per column, formats (dates, separators like `YYYY-MM-DD:amount|...`, `none` sentinels)
   - one output row per input id
   - required extra files inside `code.zip` (September 2026 added `evaluation/usage_report.md`)
   - log format: the session-start entry, the per-turn entry, and the `tool=` rule
   - forbidden inputs (organizer-only files outside `dataset/`, hardcoded labels)
   - determinism, secrets in env vars, setup and run instructions in the code package
   - the conflict-resolution order and tie-break order, if the problem states them
4. **Diff against the last edition you know.** `scripts/contract_extract.py --diff OLD NEW` lists added, changed and removed requirement lines (a heuristic; still read both files). New sections are where the new traps are. Known changes so far:
   - June 2026: onboarding flow with a recited rules agreement; log entries had an `Agent:` line in session start.
   - September 2026: onboarding replaced by a session-start greeting with a countdown; mandatory `tool=` line in **every** entry (invalid if missing, blank, a placeholder, a generic label like `AI`, only a model name, or a different harness); mandatory submission-link rule; `evaluation/usage_report.md` required; a stated conflict-resolution order; sample rows declared "not labels".
5. **Write the MUST list into the kickoff prompt** (`prompt-templates.md` §1) so the coding agent builds against it from the first turn.
6. **Turn the MUST list into checks.** Most map to a bundled script:
   - log format: `scripts/check_log.py log.txt --expect-tool "<exact harness name>"`, with `--profile` when the format matches a shipped edition other than the default (`--list-profiles`)
   - output shape: `scripts/preflight.py output.csv --template dataset/output.csv --inputs <input csv> --id-col <id>` plus `--enum` for each allowed-value column
   - usage report: log every model call to JSONL from the first paid call (`assets/usage_log_schema.md`), then `scripts/usage_report.py`
7. **Note the deadline with timezone** and when the interview window opens.

## The `tool=` rule in practice

- The value is the harness name, not the model. For Claude Code, `tool=Claude Code`. Not `claude-opus-…`, not `AI`, not `assistant`.
- Illustrative `--expect-tool` values per agent (illustrative; copy the exact string the starter's AGENTS.md and your harness produce): `"Claude Code"`, `"Codex"`, `"Cursor"`, `"OpenCode"`, `"Antigravity"`. These are product names, not names any harness was seen to report; the September 2026 starter says "Never guess the tool name."
- Sub-agents log to the same file with `parent_agent=` set.
- Run `check_log.py` after the first few turns and again before packaging. A transcript with invalid entries is a compliance miss on the 10% artifact and visible to the code grader.

## The usage report in practice

The report summarizes the **final full-dataset run that produced `output.csv`**: providers and model names, number of calls, input and output tokens, total and average tokens per request, estimated total and per-request cost, with per-model and overall totals when more than one model is used. It cannot be reconstructed after the fact, so log per call from the start. Cached runs that make no calls still need the report from the run that populated the cache; say which run it describes.

## Authorship

The rules say the participant must be the author. Use this skill's scripts to check your work. Do not copy them into the submission.
