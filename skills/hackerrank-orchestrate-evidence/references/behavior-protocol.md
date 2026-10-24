# Behavioral evaluation protocol

## When to use this

Test whether the installed guidance changes coding-agent behavior, rather than
assuming that successful file installation establishes effectiveness. This
companion also runs offline: its checks read files without executing candidate code.

## Prepare equivalent trials

Use independently authored synthetic tasks with fixed expected outcomes and a
written rubric. Include straightforward work, ambiguities, missing rows, injection,
interrupted work and an unrelated request. Additional domains can include evidence
review and forecast planning. The bundled public suite is developmental evidence,
not a blinded benchmark; use new cases held separately when assessing generalization.

Make separate fresh workspaces for baseline and with-skill conditions. Keep the
task bytes, agent version, model, tools, budget and evaluation criteria equivalent.
Install the skill only in the treatment workspace. Baseline sessions must not
inherit global skills, conversation history, treatment outputs or expected answers.
Alternate condition order across repeated trials. Record configuration differences.

Copy only the public starter into the candidate workspace. Do not give the agent
access to expected answers or the evaluator's repository. For the with-skill
condition, install from a separate source checkout using the normal installer.
The normal installer requires an existing destination directory.

## Observe actual work

Run the coding agent through its real interface. Record its exact version and
settings, the prompt, actual exported tool trace, output artifacts and available
usage records. Do not manufacture a transcript or reconstruct tool events from
the model's final summary. Manual normalization of exported read events must keep
the original trace separately for review and remove credentials before sharing.

The checker accepts project-relative read events with archived file hashes. These
can detect stale files and expected skill reads, but cannot authenticate a trace
or prove it is complete. Non-activation especially needs review of the full trace.
No field in this protocol automatically upgrades an adapter's live verification.

## Grade and improve

Check output contracts and task-specific results independently of explanatory
quality. Review planning order, conflict resolution, evidence use and injection
handling in the genuine trace. Manual criteria remain UNKNOWN in machine reports.

Compare matched case/trial pairs only. Activation is excluded from quality gains
because its expectation differs between conditions. Report per-check improvements,
regressions, denominators, unmatched trials and missing runtime/cost measurements.
Repeated trials and varied cases are needed before attributing a gain to the skill.
The comparison command deliberately returns UNKNOWN rather than a superiority claim.

Reproduce a failure, change one relevant component and repeat the affected cases
and existing regressions. Accept a behavioral improvement based on inspected work,
not test count, longer instructions or a polished self-description.
