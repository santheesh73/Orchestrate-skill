# Loop patterns

The hard rules live in `SKILL.md`; this file gives the detail behind the loops they reference.

## Contents
1. Agent loop
2. Plan → Build → Review
3. Iteration loop with change record
4. Prompt relay loop
5. Verify-before-trust loop
6. Per-row safety loop
7. Phase gates and the 24-hour budget

---

## 1. Agent loop

The model chooses which tool to call, with what arguments, how many times, and when it is done. Code supplies only:

- a **step cap** (a named constant, typically 6 to 10 tool rounds)
- a **fallback** when the cap is hit or no valid final answer arrives (an honest escalation or safe-default row)
- a **final-answer contract** (a typed, validated structure, never free text that code then parses loosely)

What graders look for is a loop **a reviewer can find and read in ten seconds**: one named function or graph, explicit termination, prompts and tool descriptions in named files or constants. A framework is fine. The May 2026 winner built on `langchain.agents.create_agent` (VERIFIED in its code); a raw API loop is just as acceptable when it is as easy to find. What fails is a "loop" that is really a hardcoded decision tree.

Tool design is prompt engineering:
- Fewer, well-chosen tools. One tool with modes (search, read, grep) beat many narrow tools in the May winner.
- Each description says what the tool returns on no match (an empty list, not an error) so the model checks explicitly.
- Errors are informative so the agent can recover. Tools are unit-testable without the model.
- The deterministic core is exposed as tools; the model never does arithmetic.
- Untrusted content (messages, documents, image text) is fenced and treated as data.

## 2. Plan → Build → Review

Every cycle: state the plan, the alternatives and why you picked one; build with specific instructions; review, including rejecting your own first draft out loud with a reason. Say which phase gate you are in at the start of each cycle. The transcript is scored on direction and ownership (35%) and iteration and verification (25%), so this has to happen from message 1. It cannot be retrofitted.

Record who decided in `assets/decision_log.md` (me / AI suggested and I accepted / AI suggested and I rejected). That feeds both the transcript and the interview honesty score.

## 3. Iteration loop with change record

Before touching anything, compute the **ceiling**: how many sample rows does this gap touch, and how many are wrong because of it versus unrelated causes? A two-row ceiling is not worth an hour.

Then every non-trivial change gets a record (`assets/change_record.md`):

```
CHANGE:
REQUIREMENT:    exact line in problem_statement.md or AGENTS.md
CLAIM:
JUSTIFICATION:  why the domain says this rule should exist (not "it fixes row X")
METRIC:         label-free checks + field-level sample accuracy
BASELINE:
RESULT:
BLAST RADIUS:   rows changed on the full input set; right direction; wrong direction
COUNTERFACTUAL: disable the change; does the effect disappear?
VERDICT:        SHIP / REJECT (apply the resolution table in evaluation.md)
```

Rules:
- Diff the **full** output against the previous run after any core or extraction change (`scripts/rerun_diff.py`), not just the target field.
- Reject a large blast radius with a small gain.
- Log rejections with the number that killed them. A rejected change is strong interview material.
- If a 5% to 25% miss is directionally consistent across many rows, suspect one systematic bug (ordering, boundary dates, a conservative estimate applied twice) before many independent errors.
- Attack your own measurement. Real examples: an ablation reported "0 of 110 rows changed" because both arms used the same backend bound at import (the real answer was 5); a benchmark overwrote the submission artifact. A clean result from a broken harness is the most dangerous output.

## 4. Prompt relay loop

1. Claude (chat) writes a paste-ready prompt for Claude Code.
2. The user pastes it as the next message (the first message for kickoff).
3. The user pastes the Claude Code report back, with any artifacts.
4. Claude verifies the claims (§5), flags anything unverified, and writes the next prompt.

Prompts reference standing files by name (`AGENTS.md` sections, `.claude/skills/`, `log.txt`) instead of restating them.

## 5. Verify-before-trust loop

- Inspect real artifacts: `output.csv`, `log.txt`, test output, hashes. Run the bundled scripts rather than trusting a summary.
- Check that the code, the output and the log tell the same story (same test count, same figures).
- Re-run install and tests from a fresh environment on the exact artifact you will submit.
- Docs drift under heavy iteration. Re-derive every number from the live repo before reciting it.
- Skepticism cuts both ways: when verification confirms a surprising result, say so and drop the doubt.

## 6. Per-row safety loop

For each input row: run, validate against the output schema, retry once on a schema violation, and on any other exception log the traceback and write an honest escalation or safe-default row. Checkpoint per row so a crash resumes with only the missing rows. Assign every failure one disposition up front:

- **ABORT**: the output would be silently wrong (bad config, missing input file). Stop with a distinct exit code; write nothing.
- **DEGRADE**: the row proceeds in a named degraded state that is counted and reported.
- **FAIL ROW**: the row gets a safe-default value, is recorded as failed, and the run continues.

Never write a partial output file; it looks like a submission.

## 7. Phase gates and the 24-hour budget

```
Gate 0  Starter contract and rubric          (starter-contract.md, rubric.md)
Gate 1  Plan, decompose, pick the archetype  (archetypes/)
Gate 2  Agent architecture and typed seam
Gate 3  Robustness and adversarial cases     (before writing input handling)
Gate 4  Implement with tests; cache model records
Gate 5  Output rows and justifications        (output-csv.md)
Gate 6  Transcript hygiene                    (continuous)
Gate 7  Self-score                            (self-score.md; never skipped)
Gate 8  Interview readiness                   (interview.md)
Gate 9  Final freeze and packaging
```

Skip depth inside a gate when behind, never the gate.

Rough budget: 0–1h gates 0–1 · 1–3h gates 2–3 · 3–13h build with tests, iterate offline from the cache · 13–16h output rows and justifications · 16–18h self-score and fix the weakest artifact · 18–20h interview drill · 20–23h freeze and package · last hour buffer. About 70% of the score is not the code.
