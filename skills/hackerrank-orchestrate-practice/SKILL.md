---
name: hackerrank-orchestrate-practice
description: Rehearse the HackerRank Orchestrate AI judge interview and review transcript evidence using the participant's actual implementation, constants and measured results. Use for mock interviews, answer checks and interview readiness. Do not use for generic job interviews or fabricated participant transcripts.
---

# Practice from the implementation

Use `references/rehearsal.md` to run a short evidence-based interview. The original skill's source-derived question generator remains useful when available; this companion also works without it or a toolkit installation.

## Workflow

Inputs: implementation, constants, run evidence and optional transcript. Outputs: source-checked feedback and next questions. Missing source leaves a claim UNKNOWN; request the artifact rather than inventing an answer.

- Read the current problem, implementation, constants and run evidence. Identify unknowns when access is incomplete.
- Ask one concrete mechanism or tradeoff question at a time. Follow up on an unexplained constant, a failure path or an apparent contradiction.
- Check answers against code and real measurements. Separate factual accuracy, explanation quality and limitations. Never invent a score or claim the simulator predicts the organizer's judge.
- Review an existing transcript for visible decisions, constraints, failures and verification. A missing event cannot be reconstructed as a past conversation; suggest what to record in future work.
- Optionally use the toolkit's interview and transcript tools if already available and requested. Their structural feedback supplements factual verification.

## Hard rules

1. **Rehearse the submitted implementation.** Do not substitute a generic architecture for the code the participant must defend.
2. **Preserve honest provenance.** Distinguish measured values from spec constants and judgement calls, and volunteer uncertainty.
3. **Keep transcript history authentic.** Do not manufacture messages, timestamps, ownership or tests.
4. **Use evidence before readiness claims.** An articulate answer is not proof that the implementation behaves as described.

## Completion evidence

Return verified strengths, incorrect or unsupported answers, source locations and a short next-practice list. Use qualitative readiness unless the user supplies an explicit practice rubric; any rubric score is a practice estimate.
