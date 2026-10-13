# Changelog

## 2.1.0 (unreleased)

### Not ported from orchestrate-loop (deliberately)
- Its personal results, ranks and per-stage scores: personal data, not guidance.
- Its full-stack build checklist: a different HackerRank product, out of scope.
- Its dated next-edition plan: it goes stale after one edition; `references/edition-update.md` replaces it with a repeatable process.
- Its kit command setup that copies the toolkit's skills into `.claude/skills/`: overlapping triggers would compete with this skill.
- Its text: the repository has no license, so ideas are restated in new wording and credited.

## 2.0.0

First release in this repository. Rebuilt from the earlier `orchestrate-loop` skill.

### Fixed
- Removed the contradiction between "revert a fix that contradicts any sample row" and the noise-floor resolution table. The resolution table in `references/evaluation.md` is now the single rule: one labeled row is noise.
- Removed the contradiction between "fitted on samples" and the generalization policy. Samples motivate or falsify; the domain justifies.
- Corrected the claim that a raw Messages API loop is what scored. Graders look for a findable, readable loop; the May 2026 winner used a framework.
- Removed advice to put design decisions in the README. The code grader reads only source, so rationale lives in docstrings and comments.
- Trigger description no longer carries dates and no longer fires on generic "prompt for Claude Code" requests.
- Self-score no longer depends on an external toolkit; it degrades to bundled scripts and a manual checklist.
- Hard rules exist in one place (`SKILL.md`) instead of three copies.
- Added a license.

### Removed
- Personal results, ranks and dataset-specific notes from past editions. Their general lessons were kept in `references/archetypes/simulation-planning.md`.
- The unrelated full-stack build checklist.

### Added
- `references/rubric.md`: per-artifact sub-criteria, caps, tie-break order, where effort pays.
- `references/starter-contract.md`: first-15-minutes checklist, the `tool=` log rule, the required usage report.
- `references/archetypes/`: retrieval triage, multimodal verification, adversarial routing, simulation and planning.
- `references/output-csv.md`, `references/interview.md`, `references/self-score.md`, `references/evaluation.md`.
- Scripts: `check_log.py`, `preflight.py`, `rerun_diff.py`, `usage_report.py`, `interview_drill.py`.
- Templates: change record, decision log with who-decided column, CONSTANTS.md, usage-log schema.
- Trigger evals, script tests, structure validator, CI.
