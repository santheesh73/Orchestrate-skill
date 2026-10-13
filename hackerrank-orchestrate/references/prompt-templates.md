# Prompt templates for the coding agent

Hand the user whole blocks they can paste unchanged. Every bracket gets its value from the edition's own `problem_statement.md` and `AGENTS.md`; a schema, column, allowed value or deadline that is not in those files must not appear. If a bracket cannot be filled from the files, ask the user instead of guessing.

`[AGENT]` is the user's coding agent. Tell the user to give that agent its own harness name for `tool=`: the September 2026 starter's `AGENTS.md` requires "the exact name of the coding harness or agent writing the entry" and says the entry is invalid if it "contains only a model name, or names a different harness."

## Contents
1. Kickoff
2. Iteration protocol
3. Targeted audit
4. Output-row pass
5. Final freeze

## 1. Kickoff (opening message of the [AGENT] session)

```
AGENTS.md is already loaded and you are writing log.txt the way it requires. Continue
on every turn without being asked, putting tool=[exact harness name] on each entry. What
follows is strategy layered on top of AGENTS.md, not a substitute. Leave AGENTS.md and CLAUDE.md as is.

Submission closes: [date, time, timezone].

Cycle through Plan, Build, Review. Before any code, lay out the plan, the options you
weighed and the reason for your choice. When you discard a draft of your own, explain
why in the transcript. Open each cycle by naming the phase gate you are at.

The task, summarized in one paragraph: [from problem_statement.md].

Contract (from AGENTS.md [sections] and problem_statement.md; obey literally):
- Output: [file and location], one row per [id column] in [input file], columns in
  this exact order: [columns]
- Allowed values: [column: values, ...]
- Formats: [date format, separators, sentinels like none]
- Required extra files: [e.g. evaluation/usage_report.md inside code.zip]
- Forbidden: [organizer-only files, hardcoded labels]
- Conflict-resolution order: [if stated]
- Tie-break order: [if stated]

Architecture: the model describes, code decides. Closest known problem shape:
[archetype], so start from [its architecture in one line].
- Deterministic core (ordinary code with unit tests, never calls a model): [state
  reconstruction, normalization, simulation, ranking, format enforcement, ...]
- Model layer only: [evidence extraction into a typed record, explanation writing].
  The model never writes a final number, label or id.
- One named agent loop with an explicit step cap, a fallback, and a validated
  final-answer schema. Prompts and tool descriptions in named files.
- Cache every model record keyed by content hash and prompt version, so the decision
  layer re-runs offline with zero API calls.
- Log every model call (provider, model, input/output tokens, request id) to
  JSONL from the first paid call; we build the usage report from it.
- Per-row failures retry once, then write an honest safe-default row. Never write a
  partial output file.
- Design reasons go in module docstrings and comments beside constants, not the
  README. Keep CONSTANTS.md with a provenance column.

Samples are examples, not labels: they may motivate or falsify a rule, never justify
it alone. Before any grouping or recurrence logic, decide and state the grouping keys
and statistic per group type, justified by the domain.

First: write the plan and the contract checklist. Do not write code yet.
```

## 2. Iteration protocol (after the first working build)

```
Use this loop for every change from now on.
1. Size the ceiling first: count the sample rows this gap affects, and how many of
   them are wrong because of this gap rather than something else.
2. Write a change record for anything beyond a trivial edit:
   CHANGE / REQUIREMENT / CLAIM / JUSTIFICATION / METRIC / BASELINE / RESULT /
   BLAST RADIUS / COUNTERFACTUAL / VERDICT
   JUSTIFICATION is the domain reason, never "it fixes row X".
3. Whenever the core or the extraction step changes, compare the ENTIRE output with
   the previous run and report how many rows changed in each column.
4. Verdict by this table: one labeled row is noise; revert if a label-free check
   regresses, or if two or more labeled rows regress and your reasoning does not
   explain them.
5. Log every rejection with the number that killed it.
Report each change as its change record.
```

## 3. Targeted audit (one bounded check)

```
A single, bounded check. It has nothing to do with [closed investigation].
Pattern: [exact code pattern + why it bites, e.g. a gate that checks whether a
free-text field the model wrote is non-empty].
1. List each occurrence.
2. For each one, decide whether a realistic model output could slip past it. Boolean
   and enum fields cannot; note that and continue.
3. For any real case, measure how often it happens using the cached records you
   already have, and demonstrate it by executing the code.
When there are no real cases, report that in one line and end the check. Do not go
looking for a milder variant.
```

## 4. Output-row pass

```
Output-row pass. No architecture changes.
1. Group rows by the model's proposed value near each class boundary in [column].
   List the rows where the deciding fact is ambiguous.
2. For each boundary, write a resolved definition (what puts a row on each side) from
   problem_statement.md and the domain. Put the definitions in the prompt; do not
   tune numeric thresholds against samples.
3. Rewrite justifications from logged facts: evidence id + rule that fired + why.
   Flag any justification that would read the same on another row.
4. Confirm the output is not collapsing onto one value (all-escalate is invalid).
5. Run the preflight check and the full-output diff; report both.
```

## 5. Final freeze

```
Last audit of the frozen files, where every claim needs evidence. Do not predict a
score, percentage or rank; describe likely outcomes in words.
1. Re-derive every number cited in code comments, README and CONSTANTS.md from the
   live repo (test counts especially).
2. Run from a fresh clone and fresh environment using only the README's steps.
3. Run the full dataset once; confirm the usage report describes exactly this run.
4. Check that code.zip, output.csv and log.txt agree with each other. Confirm no secrets,
   no organizer-only files, AGENTS.md and CLAUDE.md unchanged.
Finish with the words TECHNICAL FREEZE, then the three most valuable non-code tasks left,
highest value first.
```
