# AGENTS.md (synthetic edition: Locker Desk)

## 1. Rules
- You must read problem_statement.md in full before writing code.
- Never commit secrets. Read API keys from environment variables.
- Do not use files outside `dataset/` as inputs.
- The submitted code.zip must include `evaluation/usage_report.md`.

## 2. Log format
Append one entry per turn to log.txt. Append only; never rewrite earlier entries.

Every SESSION START and per-turn log entry must contain exactly one non-empty `tool=` line
with the exact name of the coding harness writing the entry. An entry is invalid if
`tool=` is missing, blank, a placeholder, a generic label such as `AI`, or only a model name.

```
## [ISO-8601 TIMESTAMP] SESSION START
tool=<exact_harness_name>

## [ISO-8601 TIMESTAMP] <short title, max 80 chars>
User Prompt (verbatim, secrets redacted):
<prompt>
Agent Response Summary:
Actions:
Context:
tool=<exact_harness_name>
```
