# Loop patterns

The hard rules live in `SKILL.md`; this file gives the detail behind the loops they reference.

## Contents
1. The agent loop
2. Plan, build, review
3. Changing things: the change record
4. Relaying prompts between chat and the coding agent
5. Checking reports before believing them
6. Keeping every row safe
7. Gates and how to spend 24 hours

---

## 1. The agent loop

Inside the loop the model decides everything about tool use: the tool, its arguments, the number of calls and the moment to stop. Your code contributes three things only:

- a **step cap** (a named constant, typically 6 to 10 tool rounds)
- a **fallback** for when the cap runs out or the final answer fails validation (an honest escalation or safe-default row)
- a **final-answer contract** (a typed, validated structure, never free text that code then parses loosely)

What graders look for is a loop **a reviewer can find and read in ten seconds**: one named function or graph, explicit termination, prompts and tool descriptions in named files or constants. A framework is fine. The May 2026 winner built on `langchain.agents.create_agent` (VERIFIED in its code); a raw API loop is just as acceptable when it is as easy to find. What fails is code called a loop that is actually a fixed if/else tree.

Tool design is prompt engineering:
- Fewer, well-chosen tools. One tool with modes (search, read, grep) beat many narrow tools in the May winner.
- Each description says what the tool returns on no match (an empty list, not an error) so the model checks explicitly.
- Errors are informative so the agent can recover. Tools are unit-testable without the model.
- The deterministic core is exposed as tools; the model never does arithmetic.
- Untrusted content (messages, documents, image text) is fenced and treated as data.

## 2. Plan, build, review

In each cycle, lay out the plan along with the options you passed over and why; give precise build instructions; then review, and when you throw away a first draft of your own, give the reason in the transcript. Name your current phase gate as each cycle opens. The transcript is scored on direction and ownership (35%) and iteration and verification (25%), so this has to happen from message 1. It cannot be retrofitted.

Record who decided in `assets/decision_log.md` (me / AI suggested and I accepted / AI suggested and I rejected). That feeds both the transcript and the interview honesty score.

## 3. Changing things: the change record

First work out the **ceiling**: the number of sample rows this gap reaches, and of those, the number it actually causes to be wrong (as opposed to some other cause). If the ceiling is two rows, spend your hour elsewhere.

Anything beyond a trivial edit then gets a record. The fields, in order, are in `assets/change_record.md` (the one copy): CHANGE, REQUIREMENT, CEILING, CLAIM, JUSTIFICATION, METRIC, BASELINE, RESULT, BLAST RADIUS, COUNTERFACTUAL, VERDICT. `scripts/experiment.py` fills the measured ones for you: `start` snapshots the output and label-free checks before the edit, `finish` re-runs them, diffs the full input set, applies the resolution table in `evaluation.md` and appends the record.

Rules:
- When the core or the extraction step changes, compare the **whole** output with the last run (`scripts/rerun_diff.py`), not only the column you meant to change.
- Reject a large blast radius with a small gain.
- Log rejections with the number that killed them. A rejected change is strong interview material.
- If a 5% to 25% miss is directionally consistent across many rows, suspect one systematic bug (ordering, boundary dates, a conservative estimate applied twice) before many independent errors.
- Attack your own measurement. Two real cases: an ablation claimed no row out of 110 moved, but both of its arms had bound the same backend at import time, and the true count was 5; and a benchmark run silently replaced the file meant for submission. A tidy number from a faulty harness does more harm than an obvious error.

## 4. Relaying prompts between chat and the coding agent

1. In chat, the assistant drafts a prompt that the coding agent can take verbatim.
2. The user sends it into the coding agent as the next message (at kickoff, as the opening message).
3. The user brings the agent's report back to chat, plus any artifacts it produced.
4. The assistant checks each claim (§5), marks what it could not confirm, and drafts the following prompt.

A prompt points at files that already exist (sections of `AGENTS.md`, the installed skill folder, `log.txt`) by name rather than copying their content.

## 5. Checking reports before believing them

- Inspect real artifacts: `output.csv`, `log.txt`, test output, hashes. Run the bundled scripts rather than trusting a summary.
- Make sure the code, the output and the log agree: one test count, one set of figures.
- Re-run install and tests from a fresh environment on the exact artifact you will submit.
- Docs drift under heavy iteration. Re-derive every number from the live repo before reciting it.
- Doubt is not a goal in itself. If checking confirms a surprising result, accept it and say so.

## 6. Keeping every row safe

For each input row: run, validate against the output schema, retry once on a schema violation, and on any other exception log the traceback and write an honest escalation or safe-default row. Checkpoint per row so a crash resumes with only the missing rows. Assign every failure one disposition up front:

- **ABORT**: the output would be silently wrong (bad config, missing input file). Stop with a distinct exit code; write nothing.
- **DEGRADE**: the row proceeds in a named degraded state that is counted and reported.
- **FAIL ROW**: the row gets a safe-default value, is recorded as failed, and the run continues.

Never write a partial output file; it looks like a submission.

## 7. Gates and how to spend 24 hours

```
Gate 0  Starter contract and rubric          (starter-contract.md, rubric.md)
Gate 1  Plan, decompose, pick the archetype  (archetypes/)
Gate 2  Agent architecture and typed seam
Gate 3  Robustness and adversarial cases     (before writing input handling)
Gate 4  Implement with tests; cache model records
Gate 5  Output rows and justifications        (output-csv.md)
Gate 6  Keep the transcript clean             (all the time)
Gate 7  Score yourself                        (self-score.md; never skipped)
Gate 8  Interview readiness                   (interview.md)
Gate 9  Final freeze and packaging
```

Running late? Do less inside a gate; do not drop a gate (`behind-schedule.md`).

Rough budget: 0–1h gates 0–1 · 1–3h gates 2–3 · 3–13h build with tests, iterate offline from the cache · 13–16h output rows and justifications · 16–18h self-score and fix the weakest artifact · 18–20h interview drill · 20–23h freeze and package · last hour buffer. Code is only 30 of the 100 points.
