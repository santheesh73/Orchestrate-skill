# Live coding-agent verification

## Current evidence status

**New universal-adapter live discovery, invocation and effectiveness: UNKNOWN.**
Version 3.2 adds the procedure and executable local graders; it does not claim a
new live model run. Executable discovery, successful installation, synthetic
controls and source-bound read records are different kinds of evidence.
Historical original-core verification remains scoped as described in
[COMPATIBILITY.md](COMPATIBILITY.md). Do not change those statuses from simulated tests.

## Start with one actual runtime

1. Record the installed agent version, chosen model, settings, tool access and
   budget. Use a fresh session and a disposable prepared project.
2. Inspect the installation dry-run, install the skill and run doctor. Confirm
   the agent's real interface is open in that project.
3. Invoke hackerrank-orchestrate. Export genuine tool evidence showing the exact
   file it read and the relevant references it opened. Preserve the original
   export and hashes of archived files; remove secrets before sharing.
4. Run clear-contract and inspect the actual artifacts and development sequence.
   A model saying it read the skill is insufficient.
5. Use another fresh session for unrelated-request. Inspect the complete trace
   for accidental activation; an empty export cannot establish non-activation.
6. Repeat runs and the remaining behavioral cases. Record failures and unknown
   evidence; do not extrapolate one successful case to every version or agent.

Use the [paired protocol](BEHAVIOR_EVALUATION.md) for with/without-skill comparisons.
Some case prompts explicitly request the skill: these test invocation and behavior,
not spontaneous discovery. Test implicit discovery separately with prompts that
do not name the skill and disclose the changed condition.

## Publish a reviewable record

Record date, source revision, OS, agent version, model/settings, adapter route,
project isolation, actual prompt, trial IDs, original trace locations, artifact
hashes, grader revision, objective findings, semantic review and observed limits.
Label runtime/cost as unavailable when unmeasured. An independent reviewer should
be able to distinguish a genuine runtime record from synthetic grader fixtures.

A read-event checker validates supplied records but cannot authenticate them.
Only publish VERIFIED for the exact mechanism and version independently reviewed;
retain UNKNOWN elsewhere. No version-detection command or API credential inspection
is necessary to run the offline suite.
