# Adversarial audit (2.4.0)

Failure it prevents: a capability that reads as working but has never been made to fail. Every row below names where the claim is enforced, the test that fails when the enforcement is broken, and how that was shown. `tests/test_audit.py` checks that every path cited here exists.

Labels: **MEASURED** means run on 2026-10-13 and the output recorded; **VERIFIED** means read in the primary source that day; **INFERRED** means reasoned, not run. Verdicts: **OK** (a mutation of the enforcement makes a test fail), **WEAK** (no test failed when it was mutated, or no checkable artifact), **BROKEN** (a reproduced defect).

How the verdicts were measured: a mutation harness (kept outside the repository) copied the tree, applied one source edit that breaks one claim, and ran the validator plus the full suite under `-W error`. A mutation that no test caught is a WEAK row. Round 1 ran 39 mutations on the 2.3.0 tree: 24 killed, 15 survived (MEASURED). Round 2 ran 27 on the fixed tree (the 15 survivors where the target still existed, plus 13 for the new code): 25 killed, 2 survived, and both got a test (MEASURED). Round 3 is in the last section.

## 1. Hard rules (`hackerrank-orchestrate/SKILL.md` lines 41 to 54)

`tests/test_audit.py` `HardRules` pins the clauses that carry each rule's meaning, checks there are 14, and checks each heading appears in no other skill file. "Judgement" rows cannot be checked by a script; the reason is in the test's `RULES` table.

| Rule | Where enforced | Test that fails when it is broken | Before | After |
|---|---|---|---|---|
| 1 (starter files) | `hackerrank-orchestrate/scripts/selfcheck.py` `starter` (new) | `StarterIntact`; mutation R01 | WEAK: rewording it to "rewrite AGENTS.md freely" passed every test (MEASURED) | OK (MEASURED) |
| 2 (contract literally) | `hackerrank-orchestrate/scripts/check_log.py` line 265, `hackerrank-orchestrate/scripts/preflight.py` | `test_scripts.CheckLog`; mutation R02 | OK (MEASURED) | OK |
| 3 (samples) | `hackerrank-orchestrate/scripts/corpus_literals.py` | `test_scripts.CorpusLiterals`; mutation R03 | OK (MEASURED) | OK |
| 4 (one row is noise) | `hackerrank-orchestrate/scripts/experiment.py` `resolve()` (new); `hackerrank-orchestrate/references/evaluation.md` §4 | `test_experiment.ResolutionTable`; mutations R04, R04b | WEAK: no code applied it, and the table read two ways (see §4) (MEASURED) | OK (MEASURED) |
| 5 (grouping first) | judgement | `HardRules`; mutation R05 | WEAK (MEASURED) | OK: wording pinned (MEASURED) |
| 6 (no free-text branch) | judgement; behavioral scenario 3 | `HardRules`; mutation R06 | WEAK (MEASURED) | OK: wording pinned |
| 7 (change record) | `hackerrank-orchestrate/assets/change_record.md`; `experiment.py finish` writes it | `TemplatesAgree`, `test_experiment.ExperimentLoop`; mutations R07, T_change_record | WEAK; `hackerrank-orchestrate/references/loop-patterns.md` §3 kept a copy that had lost CEILING (VERIFIED) | OK (MEASURED) |
| 8 (rationale in source) | judgement | `HardRules`; mutation R08 | WEAK (MEASURED) | OK: wording pinned |
| 9 (constants provenance) | `hackerrank-orchestrate/scripts/interview_drill.py` `missing_constants` | `test_scripts.InterviewDrill`, `TemplatesAgree`; mutations R09, T_constants | OK for the script; WEAK for the template labels (MEASURED) | OK |
| 10 (counterfactuals) | judgement; the COUNTERFACTUAL line of the record | `HardRules`; mutation R10 | WEAK (MEASURED) | OK: wording pinned |
| 11 (one bad row) | `hackerrank-orchestrate/scripts/preflight.py` line 177 | `test_scripts.Preflight`; mutation R11 | OK (MEASURED) | OK |
| 12 (self-score) | `hackerrank-orchestrate/scripts/selfcheck.py` | `test_scripts.SelfCheck`, `NothingExaminedIsUnknown`; mutations R12, N_preflight, N_constants | BROKEN: selfcheck printed PASS for an output with no data rows, a constants check over zero constants, and a corpus check over zero source files (MEASURED) | OK (MEASURED) |
| 13 (interview drill) | `hackerrank-orchestrate/scripts/interview_drill.py` | `test_scripts.InterviewDrill`; mutation R13 | OK (MEASURED) | OK |
| 14 (guarantee boundary) | judgement; core principle | `HardRules.test_core_principle_is_intact`; mutation R14 | WEAK (MEASURED) | OK (MEASURED) |

## 2. Scripts (`hackerrank-orchestrate/scripts/`)

Every script was also BROKEN on a named pipe: given one as an input path, 18 invocations across eight scripts and `tools/run_trigger_evals.py` hung until killed (MEASURED, hostile-input round 2). Each now refuses it with exit 2.

| Script | Claim | Test that fails when it is broken | Before | After |
|---|---|---|---|---|
| `hackerrank-orchestrate/scripts/check_log.py` | One valid `tool=` line per entry; model names rejected | `test_scripts.CheckLog`; mutations R02, S_check_log | OK (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/claim_audit.py` | Exit 3 when nothing could be checked | `test_scripts.ClaimAudit`; mutation S_claim_audit | OK (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/contract_extract.py` | A checklist of requirement lines | `NothingExaminedIsUnknown`, `OutputNeverOverwritesInput`; mutation N_contract | BROKEN: exit 0 with an empty checklist; `--out` into a new folder failed; `--out starter/AGENTS.md` overwrote the contract with exit 0 (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/corpus_literals.py` | Code literals copied from the dataset | `NothingExaminedIsUnknown`; mutations R03, S_corpus_literals, N_corpus | BROKEN: exit 0 ("clean") with no source file or no dataset value (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/experiment.py` (new) | Applies the resolution table to one change | `test_experiment`; mutations R04, X_exp_floor, X_exp_label, X_exp_blast | none | OK (MEASURED) |
| `hackerrank-orchestrate/scripts/interview_drill.py` | Questions from your own code | `NothingExaminedIsUnknown`, `OutputNeverOverwritesInput`; mutations R09, R13, S_interview_drill, N_drill | BROKEN: exit 0 on a folder with no source file; `--out` could overwrite a source file (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/preflight.py` | Header, ids, enums, blanks | `test_scripts.Preflight`, `NothingExaminedIsUnknown`; mutations R11, S_preflight, N_preflight | BROKEN: "0 rows checked", exit 0, on a header-only file (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/rerun_diff.py` | Churn between two runs; the noise floor | `NothingExaminedIsUnknown`; mutations S_rerun_diff, N_rerun | BROKEN: "identical", exit 0, on two empty runs; WEAK: ignoring ids missing from one run passed every test (MEASURED) | OK |
| `hackerrank-orchestrate/scripts/selfcheck.py` | Skipped or empty means UNKNOWN | `test_scripts.SelfCheck`, `NothingExaminedIsUnknown`, `StarterIntact`; mutations R12, S_selfcheck, N_constants, N_starter | BROKEN (see rule 12) | OK |
| `hackerrank-orchestrate/scripts/usage_report.py` | Builds the usage report | `test_hostile_inputs.UnwritableOut`, `OutputNeverOverwritesInput`; mutations S_usage_report, N_out | BROKEN: the documented `--out code/evaluation/usage_report.md` failed with exit 2 on a fresh tree; `--out` onto the log overwrote it (MEASURED) | OK |

## 3. Archetypes, templates, edition profiles, tools

| Item | Where enforced | Test or check | Before | After |
|---|---|---|---|---|
| `hackerrank-orchestrate/references/archetypes/index.md` routes to each page | `tools/validate_skill.py` | mutation A_index killed | OK (MEASURED) | OK |
| `hackerrank-orchestrate/references/archetypes/adversarial-routing.md`, `hackerrank-orchestrate/references/archetypes/multimodal-verify.md`, `hackerrank-orchestrate/references/archetypes/retrieval-triage.md`, `hackerrank-orchestrate/references/archetypes/simulation-planning.md` | `ARCHETYPE_SECTIONS` in `tools/validate_skill.py` | mutations A_adversarial, A_multimodal, A_retrieval, A_simulation killed | OK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/change_record.md` | `TemplatesAgree` | mutation T_change_record | WEAK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/decision_log.md` | `TemplatesAgree` | mutation T_decision_log | WEAK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/CONSTANTS.md` | `TemplatesAgree` | mutation T_constants | WEAK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/usage_log_schema.md` | `TemplatesAgree` feeds its example to usage_report | mutation T_usage_schema | WEAK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/editions/sept-2026.json` | `check_log.py` profiles | mutation E_sept killed | OK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/editions/june-2026.json` | same | mutation E_june killed | OK (MEASURED) | OK |
| `hackerrank-orchestrate/assets/editions/template.json` | `tools/validate_skill.py` | mutation E_template killed | OK (MEASURED) | OK |
| `tools/validate_skill.py` | date-free description | mutation X_validate killed | OK (MEASURED) | OK |
| `tools/package_skill.py` | clean zip and installs | `ToolGaps`, `OutputNeverOverwritesInput`; mutation X_package | WEAK; BROKEN: `--install` onto the source's parent with `--force` replaced the source folder, deleting what packaging excludes (MEASURED) | OK |
| `tools/footprint.py` | budgets | mutation X_footprint killed | OK (MEASURED) | OK |
| `tools/run_trigger_evals.py` | precision and recall | `ToolGaps`; mutation X_trigger | WEAK: precision computed as tp/(tp+fn) passed every test (MEASURED) | OK |

## 4. Loops (`hackerrank-orchestrate/references/loop-patterns.md`)

| Loop | Inputs | Artifact | Stop condition | Failure prevented | Checkable by | Verdict |
|---|---|---|---|---|---|---|
| Agent loop (§1) | input row, tools | typed final answer | step cap or a validated answer | free text parsed loosely; an if/else tree called a loop | judgement (the interview drill lists caps and constants) | WEAK: no script can find a loop in arbitrary code (INFERRED) |
| Plan, build, review (§2) | plan, options passed over | `hackerrank-orchestrate/assets/decision_log.md` | gate named and reviewed | ownership the transcript cannot show | `TemplatesAgree` (who-decided column) | OK for the artifact; its use is judgement |
| Change record (§3) | output, label-free checks, labels | change record from `experiment.py finish` | a SHIP, REJECT, NOISE or UNKNOWN verdict | a verdict worked out by hand two ways | `hackerrank-orchestrate/scripts/experiment.py`; `test_experiment` | BROKEN before: the table gave two verdicts for a one-row gain and for a +3/-2 change (MEASURED in the dry run); OK after |
| Prompt relay (§4) | agent report | the next prompt | every claim checked or marked | a pasted report believed as is | behavioral scenario 4; `hackerrank-orchestrate/scripts/claim_audit.py` | OK (MEASURED, 2 of 2 runs) |
| Verify before trust (§5) | artifacts, hashes, counts | script output | figures agree | drifted docs recited as fact | `hackerrank-orchestrate/scripts/claim_audit.py`, `hackerrank-orchestrate/scripts/selfcheck.py` | OK |
| Per-row safety (§6) | each input row | complete output file | every input id has a row | a crash that loses rows | `hackerrank-orchestrate/scripts/preflight.py` (missing ids) | OK |
| Phase gates (§7) | the clock | gate named in the transcript | Gate 9 frozen | a gate dropped when late | `hackerrank-orchestrate/scripts/selfcheck.py` for gate 7 only | WEAK for the other gates: they are judgement (INFERRED) |

The dry run (`tests/test_audit.py` `DryRun`, on `tests/fixtures/edition_synth/`, an invented edition) chains contract extraction, a flawed CSV that fails preflight, the fixed CSV, the noise floor from `rerun_diff.py`, an experiment whose one-row gain comes out NOISE, `check_log.py` on a good and a bad log, `usage_report.py --out` into a new folder, selfcheck and the drill. Each output is the next input and nothing needs the network or an install (MEASURED). Friction it found and the fix: the noise floor had to be copied by hand (now `--noise-floor`), better and worse labeled rows had to be counted by hand (now `experiment.py`), and the documented `--out` example failed (fixed). Not fixed: no script checks cross-column rules such as "locker_size is none unless the action is assign"; that stays a judgement for the participant's own tests.

## 5. Claims re-read against primary sources (2026-10-13)

| Claim | Source | Result |
|---|---|---|
| Every figure from the May 2026 post-mortem in `hackerrank-orchestrate/references/rubric.md` | hackerrank.com/blog/behind-the-scenes-of-hackerrank-orchestrate | VERIFIED, except one sentence that merged two findings ("substantial explanations scored higher" and "specificity correlated at r = 0.583"); now two findings |
| The May winner built on `create_agent` | its repository, shallow clone, read and not run | VERIFIED |
| June and September 2026 starter rules behind the edition profiles | interviewstreet starter repositories | VERIFIED |
| An October 2026 starter | interviewstreet lists may26, june26, august26 and september26 only | UNKNOWN: not public yet; no name was guessed |

## 6. Behavioral scenarios (fresh agents)

A rubric was written before any run. Each scenario ran twice, each time in a new agent that saw only the skill folder and the synthetic edition. 12 of 12 runs passed and each scenario passed 2 of 2 (MEASURED). That is a small sample, from one model family, on one invented edition. No skill text was changed for them.

| Scenario | Trap | Pass condition |
|---|---|---|
| 1 | `CLAUDE.md` is `@AGENTS.md` | both files byte-identical afterwards |
| 2 | a sample row contradicts a rule | the rule's 30 kg limit kept |
| 3 | a free-text field as a branch condition | branches on a boolean or an enum |
| 4 | a report claims "all 40 tests pass" | the real count (31) and row count found |
| 5 | `tool=` must name the harness | the harness named, never the model |
| 6 | kickoff prompt | complete, constrained, no invented figure |

## 7. Hostile-input rounds

| Round | Method | New defects |
|---|---|---|
| 1 | 52 targeted cases on new and changed code | 5 tracebacks in `experiment.py` on a damaged `meta.json`; a ragged CSV, an unstartable `--check` and `--timeout 0` accepted |
| 2 | 6 new input classes added to `tests/test_cli_matrix.py` (named pipe, UTF-16, duplicate and blank header cells, 20,000 columns, an open quote) | 18 hangs on a named pipe |
| 3 | change-record targets | `finish --record output.csv` appended the record to the pipeline's own output |
| 4 | `--out` onto each script's own inputs | 4 inputs overwritten with exit 0, `AGENTS.md` among them; `package_skill.py` replacing its source |
| 5 | 600 seeded byte-level fuzz runs over ten scripts | none |

Round 5 found nothing new, so the rounds stopped there (MEASURED).
