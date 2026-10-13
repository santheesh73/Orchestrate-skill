# Prompt templates for Claude Code

Write these as complete, paste-ready blocks. Fill every bracket from the real `problem_statement.md` and `AGENTS.md`. Never invent a schema, column list, allowed value or deadline. If a bracket cannot be filled from the files, ask the user instead of guessing.

## Contents
1. Kickoff
2. Iteration protocol
3. Targeted audit
4. Output-row pass
5. Final freeze

## 1. Kickoff (first message in the session)

```
You already read AGENTS.md and are logging to log.txt per its rules. Keep doing that
every turn, unprompted, with tool=[exact harness name] in every entry. This message adds
strategy; it does not replace AGENTS.md. Do not edit CLAUDE.md.

Deadline: [date, time, timezone].

Work Plan -> Build -> Review. Before building anything, state the plan, the
alternatives you considered and why you picked one. Say out loud why you reject your
own first drafts. Tell me which phase gate you are in at the start of each cycle.

Task in one paragraph: [from problem_statement.md].

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
- Deterministic core (plain code, unit-tested, zero model calls): [state
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
From here every change follows this loop.
1. Ceiling first: how many sample rows does this gap touch, and how many are wrong
   because of it versus other causes?
2. Change record for every non-trivial change:
   CHANGE / REQUIREMENT / CLAIM / JUSTIFICATION / METRIC / BASELINE / RESULT /
   BLAST RADIUS / COUNTERFACTUAL / VERDICT
   JUSTIFICATION is the domain reason, never "it fixes row X".
3. After any core or extraction change, diff the FULL output against the previous run
   and report rows changed per column.
4. Verdict by this table: one labeled row is noise; revert if a label-free check
   regresses, or if two or more labeled rows regress and your reasoning does not
   explain them.
5. Log every rejection with the number that killed it.
Report each change as its change record.
```

## 3. Targeted audit (one bounded check)

```
One targeted check, unrelated to [closed investigation].
Pattern: [exact code pattern + why it bites, e.g. a gate on the truthiness of a
model-written free-text field].
1. Find every place it occurs.
2. For each, can the model plausibly produce a value that defeats it? Booleans and
   enums are already safe; confirm and move on.
3. If found, size it from real cached records, not in the abstract, and reproduce it
   by running the code.
If nothing is found, say so plainly and stop. Do not hunt for a weaker version.
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
Evidence-gated final audit on the frozen files. No scores, percentages or rank
predictions; describe expected outcomes qualitatively.
1. Re-derive every number cited in code comments, README and CONSTANTS.md from the
   live repo (test counts especially).
2. Run from a fresh clone and fresh environment using only the README's steps.
3. Run the full dataset once; confirm the usage report describes exactly this run.
4. Confirm code.zip, output.csv and log.txt tell the same story. Confirm no secrets,
   no organizer-only files, CLAUDE.md unchanged.
End with TECHNICAL FREEZE and the three remaining non-code actions ordered by value.
```
