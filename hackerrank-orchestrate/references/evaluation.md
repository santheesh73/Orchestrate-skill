# Evaluation and anti-overfitting

This file holds the full decision procedure behind hard rules 3 and 4 in `SKILL.md`. Where this file and any other text disagree, this file wins.

## 1. Generalization policy

Treat the dataset as a window onto the domain. It is not the spec.

- Each rule needs a reason you can point to in the problem statement or in how the domain normally behaves.
- Samples may **motivate** a rule (they show a case exists) or **falsify** one (they show it is wrong). On their own they never justify it.
- Do not key a rule on an id, on a string lifted from the data, or a combination whose cardinality comes from sample size. Check with `scripts/corpus_literals.py`, which flags code literals that equal dataset values.
- Reject any constant that exists only because the sample's distribution happened to suggest it. A constant chosen from domain reasoning and then checked against the sample is fine; record it as JUDGEMENT or MEASURED in `CONSTANTS.md` and name the alternative you rejected.

Whenever the data shows a striking pattern, note three things: what you saw, the general lesson you took from it, and the sample-specific rule you chose not to write. This is one of the strongest interview answers available.

## 2. Anti-overfitting protocol

1. Never move a threshold so that one particular sample row comes out right.
2. Write down the reason for a rule first, implement it, and only then check the result. Trying many values and keeping the winner is not allowed.
3. Do study wrong rows to understand them. To fix one, though, you must name a class of cases broader than that single row.
4. Decide what to build from the problem and the domain; look at the labeled set afterwards, to check.
5. Warning sign: if the only honest reason you can give is "sample accuracy goes up", abandon the change.

## 3. Label-free checks come first

Label-free checks test properties of your own system and need no labels: contract valid, no ungrounded citations, no parse failures, no unexplained changes on an offline rerun, safety rules still fire on their test cases, architecture tests pass. They are true or false.

A labeled sample of 20 to 30 rows is an estimate with a wide interval. One row is 3 to 5 points. Write down how the labeled set differs from the evaluation set; when it has few adversarial or structural rows, a safety rule that never fires on it is normal and not a bug.

## 4. Resolution table (canonical)

Count labeled rows, not net movement: B = labeled rows the change made right, W = labeled rows it made wrong, N = the noise floor in rows (§5; 1 when not measured). Apply the first row that matches. `scripts/experiment.py` applies this table for you.

| Row | Label-free checks | Labeled sample | Verdict |
|---|---|---|---|
| A | Any check fails after the change (it regressed, or it was red before too: a hard gate, §6) | Any | REJECT. Revert, or fix the check first. |
| B | None run | Or no labeled row compared | UNKNOWN. Run the missing half before deciding. |
| C | Clean | 2 or more of the W rows are not explained by the change's written reason | REJECT. Revert. |
| D | Clean | B − W is at most the larger of 1 and N | NOISE. Keep only if the written reason holds; never call it an improvement. |
| E | Clean | B − W is 2 or more and above N | SHIP. Then check the blast radius on the full input set. |

Never accept or reject on a one-row difference. A gain smaller than two rows is not an improvement, in the README or in the interview.

## 5. Noise floor

Measure the model's own run-to-run variance once: re-derive the model records from cold and diff with `scripts/rerun_diff.py`. One measured case moved 3 of 110 action values (about 97% stable) and one labeled row. If your noise floor is N rows, a change worth N rows or fewer is not evidence.

## 6. Merge gates

- **Hard gates** (anything above zero blocks the merge): the output contract holds (`preflight.py`), zero ungrounded citations, zero hard parse failures, zero unexplained differences when re-run offline, architecture tests green (no corpus literals per `corpus_literals.py`, no network in the decision layer), log entries valid (`check_log.py`).
- **Review gates** (allowed only with a written reason): two or more labeled rows getting worse, many rows changing for a small net gain, a safety rule no longer firing, the output distribution collapsing onto one value (all-escalate is invalid).
- **For information, never a gate:** token counts, per-class scores with support under 5, calibration, confidence histograms.

## 7. Attack your own work

Have a model read the code looking for bugs, and accept a bug only once running the code reproduces it. In one review, that requirement cut 24 suspected bugs down to 8 real ones.

Grounding tests prove an input matters:
- **Blank-drop:** swap the evidence (image, document) for an empty one; the answer must fall back to "not enough information".
- **Swap:** change the evidence; the output must change.
- **Ablation:** remove each input a rule declares it reads; the rule must stop firing. A rule that keeps firing was passing for the wrong reason.
