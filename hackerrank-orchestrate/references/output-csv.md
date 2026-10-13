# Output CSV: the stage top finishers lose

The CSV is 30 points and is the weakest stage for most of the top 50 in public leaderboards. Many top-50 entries pair strong code with an average CSV, so getting the rows right as well is where a team pulls ahead. Reserve explicit build time for it (gate 5), not the last hour.

## 1. Contract first

Run `scripts/preflight.py` after every full run. A wrong header, a missing id or an off-enum value costs whole rows regardless of reasoning quality.

```
python scripts/preflight.py output.csv --template dataset/output.csv \
  --inputs dataset/requests.csv --id-col request_id \
  --enum "affordability_status=affordable_now|affordable_with_plan|affordable_later|not_affordable" \
  --nonempty decision_explanation
```

(Columns and values above are from September 2026; read yours from this edition's files.)

## 2. Attack the boundary calls

Rules are rarely where top finishers lost rows. The model's default proposal near a class boundary was. In one well-documented case the rule layer was never wrong; the proposal it defaulted to was.

1. For each categorical column, list the rows where the deciding fact sits near the boundary between two values.
2. Write a **resolved definition** of that boundary from the problem statement and the domain: what puts a row on each side, with a contrastive pair of examples. Contrastive pairs beat a bare list of allowed values.
3. Put the definitions in the prompt. Do not tune numeric thresholds against 25 rows.
4. For genuinely borderline reads only, a majority vote over three model calls can stabilize the call. Measure variance before claiming a gain.
5. Stop after moving a boundary a small, justified amount. Apply the resolution table in `evaluation.md`.

## 3. Justifications

A correct label with a generic justification is capped at about 70% for that row.

Template, generated from logged facts rather than free model prose:

```
<decision> because <rule or constraint that decided it> given <specific evidence:
ids, amounts, dates, quoted fact>; <the alternative that lost and why>.
```

- Name evidence ids that the agent actually read. Drop any citation that was not read (the citation guard).
- If the generated text is empty or ungrounded, fall back to a deterministic template filled from the decision record.
- Test: would this justification read the same on a different row? If yes, it is generic.
- Keep within any length or register limit the problem states.

## 4. Safety and escalation rows

- Safety is scored separately: one 0–100 score for the submission as a whole (rubric.md §2). Check the adversarial rows on their own: injected instructions in messages or images, impersonation, override demands.
- Escalate when evidence is thin, the request is high-risk, or the run failed for that row, and say why in the justification.
- Escalating everything was invalid in May 2026, and so was replying to everything (rubric.md §3). Check the output distribution after every run.

## 5. Consistency checks worth automating

- Values that must agree across columns do agree (for example a plan's amounts sum to the requested amount; a date equals the request date when the status says "now").
- Sentinels are exact (`none`, empty) as the contract states.
- Numbers are within stated bounds and formatted as the template shows.
- The rerun diff (`scripts/rerun_diff.py`) shows zero unexplained changes on an offline rerun from the cache.
