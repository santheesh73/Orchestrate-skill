# Changelog

## 2.2.1

Figures below are MEASURED in this repository unless labeled otherwise. The scripts check a participant's own work; they are not part of a submission.

### Fixed
- `claim_audit.py` exits 3 and `selfcheck.py` reports the claims section as UNKNOWN when no claim could be checked; v2.2.0 reported PASS after checking nothing. The repo's own live counts are now phrased so they are audited: 113 tests.

## 2.2.0

Figures below are MEASURED in this repository unless labeled otherwise. The scripts check a participant's own work; they are not part of a submission.

### Fixed
- Adversarial testing in three rounds ran every script and tool on hostile input; 16 reproduced defects, each now has a regression test (`tests/test_hostile_inputs.py`, `tests/test_tools.py`).
  - Round 1 (7): `usage_report.py`, `interview_drill.py`, `claim_audit.py` and `corpus_literals.py` raised tracebacks on non-UTF-8 files; `selfcheck.py` crashed on a section that is not an object, iterated a string given where a list belongs character by character, and did not resolve Windows-style relative paths; `SyntaxWarning` text from a participant's file leaked into `selfcheck.py` output, and under `-W error` that file's tests went uncounted.
  - Round 2 (6): every CSV reader raised on CR-only line endings and on fields over 131072 characters; Python 3.9 raised on NUL bytes; a dangling symlink in a code folder crashed `interview_drill.py` and stopped `corpus_literals.py`; `--out` into a missing folder raised tracebacks in three scripts; `selfcheck.py` passed a non-integer `min_length` through.
  - Round 3 (3): a non-UTF-8 `SKILL.md` or a broken symlink inside the skill crashed `validate_skill.py` and `package_skill.py`; `--out` or `--install` onto an existing file raised tracebacks.
  - Round 3 still found defects, so no clean round was reached within the three-round limit.
- Interview figures stated precisely: in the organizer's transcripts, very short answers correlated with interview score at r = −0.568 and total words at r = 0.615 (VERIFIED, May 2026 post-mortem). Top-quartile balance: 37 of the May top 50 on all four artifacts plus 11 on three is VERIFIED; the June and August readings stay INFERRED. The generic-justification cap reads "about 70 out of 100".
- The README restated several hard rules; it now links to `SKILL.md`.

### Added
- `tools/package_skill.py`: builds `dist/hackerrank-orchestrate.zip` with one top-level folder and no development files, validates the staged copy with the standalone checks, and optionally installs it (`--install DIR`, `--force`). Prevents a rejected upload or dev files shipped to users.
- `tools/footprint.py` and `FOOTPRINT_BUDGETS` in the validator (measured size plus about 10%). Prevents silent growth of the always-loaded context. Token counts are ESTIMATED as characters / 4.
- `docs/COVERAGE.md`: every rubric sub-criterion and every orchestrate-loop capability mapped to guidance and a check, with a test that every path exists. Prevents an unnoticed gap.
- Validator checks: hard-rule titles restated verbatim in `README.md` or `docs/`; broken symlinks and non-UTF-8 text files inside the skill.
- CI packages the skill, validates the installed copy with `--standalone`, and prints the footprint summary.
- Test count at the 2.2.0 release: 102.

### Changed
- `selfcheck.py` rejects a config whose sections or fields have the wrong JSON type (exit 4) instead of crashing or silently mis-checking.
- `dist/` is ignored by git.

### Not done
- Trigger accuracy against a live model: UNKNOWN. `ANTHROPIC_API_KEY` and `TRIGGER_EVAL_MODEL` were not set, so `tools/run_trigger_evals.py --live` was not run. The offline proxy is unchanged: precision 0.72, recall 0.59 (MEASURED, proxy only).
- Leaderboard per-stage figures: still INFERRED; the leaderboard was not reachable to re-derive them.
- Toolkit digest: still secondhand; the toolkit repository could not be located.
- October 2026 edition: no public starter repository, so no profile was added (UNKNOWN).
- The `v2.1.0` tag: the git proxy in the build environment refused the tag push; it has to be created on GitHub.

## 2.1.0

Figures below are MEASURED in this repository unless labeled otherwise.

### Fixed
- `check_log.py` never detected CRLF line endings; a UTF-8 BOM hid the first log entry.
- `interview_drill.py` mixed parse errors into its constants list, failed on BOM source files, and mutated its skip list between calls.
- `rerun_diff.py` silently merged duplicate columns or duplicate ids, and exited 1 instead of 2 on bad input.
- `preflight.py` did not flag duplicate header columns.
- The usage-report test leaked a file handle (visible under `-W error`).
- Claims corrected against their sources: the September interview account (the debit/credit mismatch was in the author's earlier report, and no point loss is reported), the interview format (30-minute voice; "camera on" removed as unverified), the output CSV safety score (one 0 to 100 score per submission), and the organizer's wording on escalating or replying to everything.
- The README carried a second copy of the hard rules; it now points to `SKILL.md`. `winning-approaches.md` repeated the archetype pages' guards; it now links to them.

### Added
- `scripts/selfcheck.py`: runs gate 7 from one JSON config; an unconfigured check is UNKNOWN, never PASS.
- `scripts/contract_extract.py`: drafts the MUST list from `AGENTS.md` and `problem_statement.md`, and diffs two editions.
- `scripts/corpus_literals.py`: flags ids, strings and number combinations copied from the dataset into code.
- `scripts/claim_audit.py`: flags test, row and constant counts in docs that no longer match the repo. It skips `tests/fixtures` when counting tests (configurable with `--exclude` and `--no-default-exclude`, or `exclude` in `selfcheck.json`), so a fixture project's tests are not added to the real suite's count. A root `selfcheck.json` runs the claims check on this repository.
- `assets/editions/` log-format profiles (`sept-2026`, `june-2026`, `template`) and `check_log.py --profile` / `--list-profiles`; output on the v2.0.0 fixtures is byte-identical (golden-file test). Each profile records `provenance` (VERIFIED / INFERRED / UNKNOWN) and `provenance_source`, and the validator requires both. `sept-2026` and `june-2026` are VERIFIED against section 5 of the official starters' `AGENTS.md`; in `june-2026`, the strict tool-name checks (`exactly_one`, `harness_not_model`) are INFERRED, carried over from September, because the June starter does not state them. `template` is UNKNOWN until filled.
- `references/behind-schedule.md` and `references/edition-update.md`.
- `rubric.md`: every organizer figure labeled VERIFIED (read in the post-mortem on 2026-10-13); per-stage top 1/10/50 table labeled INFERRED (secondhand; the leaderboard API was not reachable).
- `kit-repo.md`: fuller toolkit digest, labeled secondhand (the toolkit repository could not be located).
- `tools/run_trigger_evals.py`: offline lexical proxy, and an opt-in live mode that needs an API key and never runs in CI. `evals/triggers.json` grows to 44 cases (22 should trigger, 22 should not, including near misses).
- Edge-case tests and validator tests (test count at the 2.1.0 release: 74).
- `VERSION` file, credits section.

### Changed
- `tools/validate_skill.py` checks policy as well as structure: description length, dates and "do not use for" clause; body under 80 lines; one canonical copy of the hard rules; scripts listed in `SKILL.md` both ways with docstrings naming the failure they prevent; `--help` and Python 3.9 syntax; eval counts and duplicates; personal-result markers; `VERSION` matching this file; `--standalone` for an installed copy.
- CI runs on Python 3.9, 3.11 and 3.13 with `-W error`, runs every script's `--help`, the offline trigger proxy with floors (precision 0.6, recall 0.5), an install test and `selfcheck` on the fixtures.
- Passages in v2.0.0 that still followed orchestrate-loop's wording closely (the master pattern, the prompt templates, the loop and evaluation pages, the archetype pages, several hard rules and the toolkit digest) are reworded. A check for shared 8-word runs against orchestrate-loop now finds only factual matches: the leaderboard figures, the toolkit's install commands and a file name.
- Trigger accuracy against a live model remains UNKNOWN. The offline proxy measures precision 0.72 and recall 0.59 at threshold 0.3 (MEASURED, proxy only). The description was not tuned against it.

### Not ported from orchestrate-loop (deliberately)
- Its personal results, ranks and per-stage scores: personal data, not guidance.
- Its full-stack build checklist: a different HackerRank product, out of scope.
- Its dated next-edition plan: it goes stale after one edition; `references/edition-update.md` replaces it with a repeatable process.
- Its kit command setup that copies the toolkit's skills into `.claude/skills/`: overlapping triggers would compete with this skill.
- Its text: the repository has no license, so ideas are restated in new wording and credited.

## 2.0.0

First release in this repository. Rebuilt from the earlier `orchestrate-loop` skill.

### Fixed
- Removed the contradiction between an earlier rule to revert any fix that disagrees with a single sample row and the noise-floor resolution table. The resolution table in `references/evaluation.md` is now the single rule: one labeled row is noise.
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
