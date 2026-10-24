# Changelog

## 3.1.0

- Add an independent identical-input synthetic comparison with per-category false-positive/false-negative denominators, exact source revisions, hashes, timings and explicit unknown capabilities.
- Add audit-selftest: healthy, injected-defect and metamorphic controls reuse existing contract/replay validators and the new opt-in decision_ids audit. Deliberately broken-checker regressions prove the controls can fail.
- Add a closed built-in contract-audit registry. The decision_ids policy reads actual input IDs and inspects Python decision syntax without executing source. The original broader corpus scanner and every existing skill/interface remain available.
- Extend CI and clean-wheel verification to the public audit selftest. See docs/COMPETITIVE_BASELINE.md for measured results and limits; no overall superiority or live activation is claimed.
- The suite contains 231 tests, including positive, negative and metamorphic audit regressions.

## 3.0.0

- Add an offline orchestrate-toolkit CLI with documented adapters, owned installation, doctor, dry-run, backup, idempotence and safe uninstall. The community orchestrate command remains separate.
- Add explicit resumable workflow gates and structured contract/replay/usage/dependency evaluation. Commands require execution consent and use bounded argument-array execution with minimal environment forwarding.
- Preserve all original checker scripts and rules; add explicit inputs, outputs and recovery to existing skills. Add a canonical capability catalog and retain the original installation tools.
- Add lifecycle simulations, negative controls, clean-wheel smoke validation and macOS CI alongside Windows/Linux. Test count at the 3.0.0 release: 219. Live agent inference remains UNKNOWN.
- Add architecture, compatibility, CLI, contribution/security documentation, synthetic examples, audit plan and release report.

## 2.5.0

### Added
- Four self-contained companion skills under `skills/`: design, submission packaging, interview practice and optional community toolkit integration. The original main SKILL.md, name and ten checker scripts remain unchanged.
- A standard-library submission packager with an explicit JSON contract, exact archive allowlist, required usage/artifact checks, nonempty CSV coverage, input/output hashes, deterministic archive metadata and a new staged output directory. It never claims official readiness or runs target code.
- `tools/package_addons.py`: validate/package/install companions without replacing any existing skill or archive, with rollback for new files on failure and notices in each archive.
- Pinned upstream provenance and core-content hashes in `integrations/upstreams.json`; source/license notices and integration documentation. No upstream code or unlicensed loop prose is vendored.
- Behavioral packaging and preservation regressions in `tests/test_submission_package.py` and `tests/test_addons.py`.
- Test count at the 2.5.0 release: 199; platform-specific skips were reported in each run.

### Fixed
- Windows hostile-input setup no longer tries to create a forbidden newline filename; other hostile cases still run.
- LF checkout attributes prevent CRLF conversion from changing golden log results while preserving byte-sensitive AGENTS fixtures.
- CI now covers Windows and Linux. A Python smoke runner checks subprocess statuses, fixtures, repository claims, original/companion installed copies and context budgets without shell-specific pipes.
- Toolkit references now identify the actual repository and reviewed revision. Edition-specific audit assumptions, Python minimum, optional installation and estimated-score limits are explicit.

### Preserved and limited
- Existing install commands, original scripts, original trigger description and evaluation policy remain available. New companions do not expand the core context budget.
- Repository selfcheck scans current README, coverage and changelog claims; older changelog counts retain their historical release wording.
- No paid model evaluations, automatic competition uploads or external dependency installation occur in CI. See the Actions run for platform results; real multi-skill routing and hidden-grader performance remain UNKNOWN.

## 2.4.0

An adversarial audit: every hard rule, script, archetype page, template, edition profile and tool was mutated to see whether a test notices, and the scripts were attacked with hostile input. Results and evidence are in `docs/AUDIT.md`. Figures are MEASURED in this repository on 2026-10-13 unless labeled otherwise. No hard rule, rubric weight or the model-describes-code-decides principle changed meaning, with one exception, recorded under Changed: the resolution table's one-row and mixed cases, which contradicted hard rule 4.

### Fixed
- Vacuous passes. Five scripts exited 0 (clean) after examining nothing, and `selfcheck.py` printed PASS for them: `preflight.py` on a header-only output (zero data rows checked), `rerun_diff.py` on two empty runs ("identical"), `corpus_literals.py` with no source file or no dataset value, `interview_drill.py` on a folder with no source file, `contract_extract.py` with no requirement line. Each now exits 3, and selfcheck reports UNKNOWN for the output, constants (also with zero named constants) and corpus_literals sections. Tests: `NothingExaminedIsUnknown`.
- The documented `usage_report.py --out code/evaluation/usage_report.md` failed with exit 2 on a fresh tree, because the folder did not exist. `--out` now creates missing parent folders in `contract_extract.py`, `interview_drill.py` and `usage_report.py`; a parent that is a file is still exit 2. Tests: `UnwritableOut`, `DryRun`.
- `--out` onto an input overwrote it with exit 0: `contract_extract.py --out starter/AGENTS.md` (the file hard rule 1 protects), a source file or `CONSTANTS.md` for `interview_drill.py`, the usage log for `usage_report.py`. Each now refuses with exit 2. `package_skill.py --install` onto the source's parent with `--force` replaced the source folder and deleted what packaging excludes; an `--install` or `--out` that overlaps the source is now exit 2. Tests: `OutputNeverOverwritesInput`.
- A named pipe given as an input path hung 18 invocations across eight scripts and `run_trigger_evals.py`. Every bundled script and `run_trigger_evals.py` now refuse one with exit 2, and selfcheck treats one in its config as missing. Test: the `fifo` class in `tests/test_cli_matrix.py`.
- Found by the independent verification pass, each reproduced by a test that failed on the previous head: `interview_drill.py --include-tests --out` could overwrite a test file it had read, and `--out` onto a source file it skips replaced it (it now refuses any source-file `--out`); `experiment.py` gave SHIP for any change when `--labels` was the output itself, appended its record to the output when the output was missing at the guard and `--cmd` recreated it (also through a dangling link), followed a symlink planted at its `after.csv` and overwrote the labels, accepted a record inside an experiment folder (losing it or corrupting another baseline), and accepted a name ending in a newline. Its full report is unedited in the PR and the release report.
- `references/rubric.md` merged two post-mortem findings into one sentence; it now gives "substantial explanations scored higher" and "specificity correlated at r = 0.583" as separate findings, as the source does.

### Added
- `scripts/experiment.py` (`start`, `finish`, `list`): runs one change record. It stores the baseline output and label-free check results, re-runs them, diffs every row of the full output, counts labeled rows made better and worse, applies the resolution table with the measured noise floor, prints SHIP, REJECT, NOISE or UNKNOWN with the reason, and appends a record with the template's fields. It never edits the user's code or data, refuses to write its record onto its own inputs, gives UNKNOWN when no check ran or no labeled row was compared, and never gives SHIP for a one-row gain. Added because the dry run showed the verdict could not be reached reliably by hand (see Changed). Tests: `tests/test_experiment.py`, which has one or more cases per table row and parses the table itself.
- `selfcheck.py` `starter` section for hard rule 1, which had no check: it fails when `AGENTS.md` differs from the sha256 recorded at kickoff or `CLAUDE.md` lost its `@AGENTS.md` line, and prints the hash to record when none is set. Tests: `StarterIntact`.
- `docs/AUDIT.md`: one row per rule, script, archetype page, template, profile and tool, with where it is enforced, the test that fails when it is broken, and the verdict before and after; the seven loops; the claims re-read against their sources; six behavioral scenarios; five hostile-input rounds.
- `tests/test_audit.py`: the hard rules' meaning-carrying clauses and the core principle are pinned, templates must agree with the rules and with each other, every path in `docs/AUDIT.md` must exist, and the whole loop runs end to end on `tests/fixtures/edition_synth/`, an invented edition.
- Six hostile input classes in `tests/test_cli_matrix.py`: named pipe, UTF-16, duplicate and blank header cells, 20,000 columns, an open quote. Test count at the 2.4.0 release: 175.

### Changed
- `references/evaluation.md` §4, the resolution table. Defect reproduced in the dry run: a one-row labeled gain matched "Clean, Up: keep", which contradicts hard rule 4 ("never accept or reject on a one-row difference"), and a change that made three rows better and two worse matched "Up: keep" while hard rule 4 says to revert it. The table now counts better (B) and worse (W) rows against the noise floor (N) and is applied first match: A a failing check REJECT; B nothing measured UNKNOWN; C two or more unexplained worse rows REJECT; D B minus W at most max(1, N) NOISE; E otherwise SHIP. Rows C to E follow hard rule 4's wording.
- `references/loop-patterns.md` §3 no longer keeps a copy of the change record (it had lost the CEILING line); it lists the fields of `assets/change_record.md` in order, and a test keeps the two equal.
- Footprint budget for on-demand files raised from 167,000 to 200,000 characters. On-demand went from 165,077 to 198,315 (+33,238): `experiment.py` is 20,579, the exit-3, `--out` and named-pipe guards across the other nine scripts add about 11,800 (selfcheck 2,747, interview_drill 2,084, contract_extract 1,729, the rest under 1,300 each), and references about 900. The SKILL.md body went from 7,049 to 7,214 (one script row) and always-loaded from 7,867 to 8,032, both inside unchanged budgets. The description is unchanged (818), so the trigger proxy is unchanged: n=56, precision 0.76, recall 0.68.

### Not done
- Live trigger accuracy: UNKNOWN. `ANTHROPIC_API_KEY` was not set.
- The October 2026 starter: UNKNOWN. It was not public on 2026-10-13 (interviewstreet lists may26, june26, august26 and september26 only).
- Behavioral scenarios: 12 of 12 runs passed (each of 6 scenarios 2 of 2), in one model family on one invented edition. That is a small sample, not an accuracy figure.
- Running the skill in Codex, OpenCode, Antigravity, Cursor and Claude.ai: still UNKNOWN (see 2.3.0).
- No script checks cross-column rules (for example "locker_size is none unless the action is assign"), the agent loop's shape, or phase gates other than gate 7; those rows of `docs/AUDIT.md` stay WEAK by design.
- Tags `v2.1.0`, `v2.2.0` and `v2.3.0` are still missing on GitHub; the proxy refuses tag pushes.

## 2.3.0

Figures below are MEASURED in this repository unless labeled otherwise. Per-agent claims use VERIFIED (the skill was run in that agent), DOCS-READ (the agent's own docs, URL and date in `docs/INSTALL.md`) or UNKNOWN. This is a portability change; no hard rule, rubric figure or evidence label changed meaning.

### Fixed
- Installing ran each bundled script's `--help` (to validate the copy) without `-B`, so every installed skill got a `scripts/__pycache__/` folder, the dev files packaging is meant to leave out. `validate_skill.py` now runs them with `python -I -B`; a test fails on the old behavior.

### Added
- `docs/INSTALL.md`: project and global folders for Claude Code, Claude.ai, OpenAI Codex, OpenCode, Google Antigravity and Cursor, each with an evidence label, source URL, the date read (2026-10-13) and known caveats. It also has a fallback opening message and how to run the scripts with `python3 -I` on POSIX and Windows. The README points to it.
- `package_skill.py --project DIR --for {claude,agents,all}`: installs into `DIR/.claude/skills`, `DIR/.agents/skills` or both, through the existing atomic install. Every target is checked before any is written. `--install DIR` is unchanged.
- `validate_skill.py`: `docs/INSTALL.md` must exist and name all six agents, and the `SKILL.md` body must not name an agent-specific install folder.
- Tests: both layouts, two identical copies with `--for all`, an existing target without `--force` (exit 2, nothing written), a mid-copy failure that keeps the old copy, and a smoke test. The smoke test installs each layout, then runs the validator and every installed script's `--help` with `python -I`, with the proxy pointed at a closed port. Test count at the 2.3.0 release: 127.
- `evals/triggers.json`: 12 cases phrased by Codex, Cursor, OpenCode and Antigravity users (6 should trigger, 6 near misses), giving 56 cases. Offline proxy: precision 0.76, recall 0.68 (was 0.72 and 0.59 on 44 cases; the original 44 still score 0.72 and 0.59). This is a lexical proxy, not model behavior.
- `docs/COVERAGE.md` section 5, Portability.

### Changed
- Agent-neutral wording in the description, the `SKILL.md` working style, and `references/` (prompt templates, starter contract, loop patterns, interview, behind schedule): "the user's coding agent" in place of Claude Code where the text was generic. Claude Code remains where it is a literal example.
- Hard rule 1 now protects the starter's agent-instruction files: `AGENTS.md` first, and `CLAUDE.md` when it is just `@AGENTS.md`. There are still 14 hard rules.
- `references/prompt-templates.md` uses an `[AGENT]` placeholder and quotes the September 2026 starter's `tool=` rule. `references/starter-contract.md` lists illustrative `--expect-tool` values per agent, labeled as such.
- Footprint (characters): description 815 to 818, SKILL.md body 6894 to 7049, always loaded 7709 to 7867, on demand 164301 to 165077. All are within budget, so no budget was raised.

### Not done
- Claude Code: VERIFIED once only. On 2026-10-13, Claude Code 2.1.296 listed the skill from `.claude/skills/` and invoked it for one Orchestrate question, and did not invoke it for one near miss. One run of each is not a trigger-accuracy figure.
- Running the skill in Codex, OpenCode, Antigravity and Cursor: UNKNOWN. None of them is installed in the build environment. Their install folders are DOCS-READ.
- Claude.ai upload: DOCS-READ. The zip was built and its layout checked, but it was not uploaded.
- Trigger accuracy against a live model: UNKNOWN. `ANTHROPIC_API_KEY` was not set, so `--live` was not run.
- Tags `v2.1.0` and `v2.2.0` are still missing on GitHub (see 2.2.1).

## 2.2.1

Figures below are MEASURED in this repository unless labeled otherwise. The scripts check a participant's own work; they are not part of a submission.

### Fixed
- `claim_audit.py` exits 3 and `selfcheck.py` reports the claims section as UNKNOWN when no claim could be checked; v2.2.0 reported PASS after checking nothing. The repo's own live count is now phrased so it is audited (README, the latest release section, `docs/COVERAGE.md`); test count at the 2.2.1 release: 119. Older release sections keep historic counts in a form the audit does not match ("test count at the 2.2.0 release: 102"), and a test enforces that, so a past number never becomes a false mismatch.
- `package_skill.py --install --force` deleted the installed copy before copying; a failed copy left nothing. It now builds and validates the new copy beside the old one, swaps it in, and restores the old copy (folder, file or symlink, which is replaced and never followed) on any failure.
- Hostile-input hunting, four rounds, 9 reproduced defects, all fixed with a failing test first:
  - Round 1 (3): `run_trigger_evals.py` raised tracebacks on a missing, directory, non-UTF-8 or non-JSON eval or skill file, and exited 0 on an empty eval list; `check_log.py --profile` crashed on a non-object JSON and silently ignored wrong-typed or misspelled keys; four scripts did not document their exit codes.
  - Round 2 (3): JSON nested 100,000 deep raised `RecursionError` in four scripts; `usage_report.py` crashed on null records, list-valued models and NaN or infinite token counts, and summed negative or boolean counts, negative prices and a negative `--requests`; out-of-range numeric options (`--min-length 0`, negative `--show`, NaN `--threshold` and others) were accepted.
  - Round 3 (2): a console that cannot encode the data (ASCII, or cp1252 and cp437 on Windows) turned printed values into `UnicodeEncodeError` in five CLIs; `claim_audit.py --repo` naming a file reported every test claim as a mismatch against 0.
  - Round 4 (1): on Python 3.9 to 3.11 a NUL byte in a participant's `.py` file crashed `interview_drill.py` and aborted `corpus_literals.py` and `claim_audit.py`.
  - Round 4 still found a defect, so no clean round was reached within the four-round limit.

### Added
- `tests/test_cli_matrix.py`: runs all 13 scripts and tools as subprocesses against 24 hostile input classes (binary, empty, header-only, directory, nonexistent, a 3 MB field, NUL, BOM, CR-only and mixed line endings, non-UTF-8, dangling symlink, symlink loop, unreadable, spaces and unicode, a very long path, wrong JSON types, deep JSON, newline or leading dash in a name, symlink to a directory, `/dev/null`, 400,000 lines, unicode content), unwritable output paths, wrong-typed configs, out-of-range options and an ASCII console. Every run must print no traceback and exit with a documented code. Adding a case is one line. Prevents the next crash on input nobody tried.

### Changed
- Exit codes: `claim_audit.py` adds 3 (nothing checked); `run_trigger_evals.py`, `contract_extract.py`, `interview_drill.py` and `usage_report.py` now document theirs; `validate_skill.py` documents 2 for usage errors.
- No footprint budget was raised.

### Not done
- Tags: the git proxy in the build environment refused the push of `v2.1.0` (on 6790467) and `v2.2.0` (on f6d9834) again; `git ls-remote --tags origin` shows none. The owner has to create them on GitHub.
- Trigger accuracy against a live model: UNKNOWN. `ANTHROPIC_API_KEY` and `TRIGGER_EVAL_MODEL` were not set. The offline proxy is unchanged: precision 0.72, recall 0.59 (MEASURED, proxy only). The description was not changed.
- Leaderboard per-stage figures: still INFERRED; the leaderboard pages refuse automated fetches (robots) and the API was unreachable.
- Toolkit digest: still secondhand; a search found no `hackerrank-orchestrate-skills` repository.
- October 2026 edition: UNKNOWN. The challenge page (read 2026-10-13) links no starter repository, and the candidate repository names are not public. No profile was added.

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
