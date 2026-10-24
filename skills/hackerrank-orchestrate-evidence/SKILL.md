---
name: hackerrank-orchestrate-evidence
description: Verify HackerRank Orchestrate requirements, evaluate coding-agent behavior on synthetic challenge cases, compare paired skill runs and audit interview citations. Use for skill effectiveness experiments, requirement-to-artifact tracking or evidence-based hackathon readiness. Do not use for generic coding tasks, official score predictions or creating retrospective participant transcripts.
---

# Build an inspectable evidence chain

Use this companion when the participant requests behavioral evaluation or needs
to connect requirements, implementation, test results and submitted artifacts.
Preserve the existing Orchestrate skills; this is an additional verification layer.

## Workflow

- Read the current edition's requirements first. Historical examples and the
  fictional practice suite do not establish competition rules.
- For requirement coverage, follow `references/evidence-formats.md`. Connect each
  requirement to its source, implementation, actual test result and output artifact.
  Hash the files used. Missing links remain UNKNOWN; changed evidence is stale.
- For skill effectiveness, follow `references/behavior-protocol.md`. Use fresh,
  separate baseline and with-skill projects, equivalent settings and repeated
  trials. Keep expected outputs outside the agent's workspace.
- For interview preparation, cite code and measurements for each answer and state
  limitations. Run citation checks, then review whether the answer follows from
  the cited evidence. A valid citation is not a true explanation by itself.
- Use `scripts/evidence.py` for deterministic local checks. It does not launch
  agents, execute participant code, call models or upload submissions.

## Hard rules

1. **Keep trials authentic.** Export genuine tool evidence for live runs; synthetic controls are explicitly labeled and never counted as live activation.
2. **Separate integrity from meaning.** File hashes and artifact matches do not prove instruction following, citation relevance or official correctness.
3. **Compare like conditions.** Reject mismatched models, versions, budgets, task fingerprints, graders and reused workspace paths; report missing pairs.
4. **Preserve unknown outcomes.** Do not convert absent runs, unreviewed explanations or missing measurements into a passing readiness claim.

## Completion evidence

Return actual artifact results, regressions, unresolved semantic checks and exact
source locations. Label reports as local evidence. The organizer's evaluation and
the participant's final submission decision remain separate.
