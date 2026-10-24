---
name: hackerrank-orchestrate-design
description: Write or review an evidence-based DESIGN.md for a HackerRank Orchestrate submission, including its output contract, model/code seam, failure handling and validation. Use when the problem is known and the participant needs a concrete design or design review. Do not use for general software design or an unrelated hackathon.
---

# Design an Orchestrate submission

Read the current problem statement and starter instructions before choosing an architecture. If they are unavailable, identify the missing contract and produce a provisional design with explicit unknowns.

Use `assets/DESIGN.md` as an adaptable template. Draft a prompt when the user asks for one; write the design directly when requested. Preserve an existing design's useful decisions and evidence.

## Workflow

Inputs: current spec, starter rules and any existing design. Outputs: a design or requested prompt with unresolved decisions. If the contract is missing, mark the design provisional and request the missing authority; never invent it.

- Map every required output field to an observation, deterministic calculation or rule. Keep exact identifiers, enums, separators and ordering requirements.
- Define the typed observations the model returns and the code that validates and consumes them. Use a bounded agent loop only when the task benefits from tool selection; explain the architecture against the current rubric.
- Choose grouping keys before statistics or detectors. Record each constant's provenance: SPEC, MEASURED, STANDARD, BOUND or JUDGEMENT.
- For retrieval, identify source IDs actually read, an evidence budget and a recall check. For images, include blank/swap controls. Omit irrelevant sections.
- Define parse errors, missing evidence, rate limits and interruptions. Use a contract-valid fallback and resumable checkpoints where appropriate. State which failures abort the run.
- Separate offline replay determinism from fresh provider variability. Compare alternatives using actual output differences, cost and counterfactual checks.

## Hard rules

1. **The current contract governs the design.** Historical examples cannot invent current requirements.
2. **Protect the participant's existing work.** Do not replace starter instruction files, working output or unrelated skills.
3. **Ground design claims in evidence.** Mark untested behavior UNKNOWN; a design document does not prove an implementation works.
4. **Respect the requested role.** Designing does not authorize paid runs, deployment or submission.

## Completion evidence

Return the design or requested prompt, unresolved assumptions and the next observable validation. Check that each required output has a source and each failure has a disposition. A runnable pipeline is a separate build milestone.
