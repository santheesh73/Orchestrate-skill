---
name: hackerrank-orchestrate-toolkit
description: Connect the optional community orchestrate-kit to a HackerRank Orchestrate project for evaluator checks, engineering memory, transcript analysis and heuristic score review. Use when the participant requests toolkit setup or its CLI capabilities. Do not use for ordinary Python installation, official score prediction or unrelated agent projects.
---

# Optional community toolkit

The existing hackerrank-orchestrate skill remains the main playbook. This companion adds optional tooling; it does not replace existing checks. Read `references/commands.md` for verified commands, installation and audit applicability.

## Workflow

Inputs: requested operation, project path and toolkit availability. Outputs: command evidence, applicability and findings. If the toolkit is absent, use the core checks and report the optional operation UNKNOWN; do not install it implicitly.

1. Determine the requested operation and project. Prefer an existing compatible toolkit environment. Check `python -m orchestrate_kit --help` there; an absent tool is UNKNOWN, not a release failure by itself.
2. If installation is requested, use a separate Python 3.10+ environment pinned to the revision in the reference. Do not install upstream skills in bulk or replace any existing skill folders.
3. Run the relevant command against the explicit project path. Inspect applicability, skipped audits and individual findings before interpreting a summary.
4. Keep project memory and histories outside installed skill files. Record rejection evidence and what would justify reconsidering it; never seed personal results as universal facts.
5. Report measured checks separately from heuristic estimates. For missing score sections, show UNKNOWN and a possible overall range rather than a complete score. Prioritize fixes by expected benefit, time and evidence, not a score gap alone.

## Hard rules

1. **Keep toolkit integration optional.** Original scripts and manual review remain usable without it.
2. **Check edition applicability.** The bundled message-router evaluator is not a universal contract checker; a skipped check is UNKNOWN.
3. **Preserve established evaluation policy.** Existing project noise and regression rules govern conflicts; a genuine contract defect still needs fixing even when it affects one row.
4. **Treat scores as estimates.** Official scores require organizer-provided results for this exact submission; lexical interview/transcript scores cannot verify truth.
5. **Inspect execution before running checks.** Evaluators may execute project commands; run only code and operations authorized by the user.

## Completion evidence

Return the command, inspected revision, audits run/skipped, findings and next action. Explain whether each figure was measured or estimated. Installation alone is not validation of a submission.
