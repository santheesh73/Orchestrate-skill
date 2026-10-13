# Evaluation and anti-overfitting

This file holds the full decision procedure behind hard rules 3 and 4 in `SKILL.md`. Where this file and any other text disagree, this file wins.

## 1. Generalization policy

The dataset is evidence about the domain, not the specification.

- Every rule must be justifiable from the problem statement or from how the domain generally works.
- Samples may **motivate** a rule (they show a case exists) or **falsify** one (they show it is wrong). They are never its sole justification.
- No rule keyed on an id, a string copied from the data, or a combination whose cardinality comes from sample size. Add a test that greps the code for corpus literals.
- A constant whose only source is a distribution read off the sample is rejected. A constant chosen from domain reasoning and then checked against the sample is fine; record it as JUDGEMENT or MEASURED in `CONSTANTS.md` and name the alternative you rejected.

For each striking pattern in the data, write three lines: the finding, the general principle taken, and the artifact-fitted rule you refused. This is one of the strongest interview answers available.

## 2. Anti-overfitting protocol

1. No threshold is adjusted to fix a specific sample row.
2. State why the rule should exist, write it, then look at what happened. Do not sweep and keep the best.
3. Reading a wrong row to understand it is essential. Turning it into a fix needs a stated class of cases larger than that row.
4. Read the labeled set after the change, not before, to decide what to build.
5. The tell: if the honest justification is "because it improves sample accuracy", drop the change.

## 3. Label-free checks come first

Label-free checks are assertions about your own system: contract valid, no ungrounded citations, no parse failures, no unexplained changes on an offline rerun, safety rules still fire on their test cases, architecture tests pass. They are true or false.

A labeled sample of 20 to 30 rows is an estimate with a wide interval. One row is 3 to 5 points. Write down how the labeled set differs from the evaluation set; if it under-represents adversarial or structural cases, a safety rule scoring zero on it is expected, not a defect.

## 4. Resolution table (canonical)

| Label-free checks | Labeled sample | Verdict |
|---|---|---|
| Clean | Down at most 1 row | Noise. Keep if the reasoning holds. |
| Clean | Down 2 or more rows | Investigate those rows. Keep only if the stated reasoning explains them; otherwise revert. |
| Regressed | Up | Revert. |
| Regressed | Down | Revert. |
| Clean | Up | Keep, but check the blast radius on the full input set. |

Never accept or reject on a one-row difference. Do not call anything under two rows an improvement, in the README or the interview.

## 5. Noise floor

Measure the model's own run-to-run variance once: re-derive the model records from cold and diff with `scripts/rerun_diff.py`. One measured case moved 3 of 110 action values (about 97% stable) and one labeled row. If your noise floor is N rows, a change worth N rows or fewer is not evidence.

## 6. Merge gates

- **Hard gates** (no acceptable nonzero value): output contract valid (`preflight.py`), ungrounded citations 0, hard parse failures 0, unexplained changes on an offline rerun 0, architecture tests pass (no corpus literals, no network in the decision layer), log entries valid (`check_log.py`).
- **Review gates** (need a written justification): labeled regression of two or more rows, high churn for a tiny net gain, a safety rule that stops firing, the output distribution collapsing onto one value (all-escalate is invalid).
- **Diagnostic only, never gating:** token counts, per-class scores with support under 5, calibration, confidence histograms.

## 7. Attack your own work

Point a model at the code to hunt for bugs, but require every suspected bug to be reproduced by running it. In one review that filter turned 24 candidates into 8 real bugs.

Grounding tests prove an input matters:
- **Blank-drop:** replace the evidence (image, document) with a blank; the verdict must collapse to "not enough information".
- **Swap:** change the evidence; the output must change.
- **Ablation:** remove each input a rule declares it reads; the rule must stop firing. A rule that keeps firing was passing for the wrong reason.
