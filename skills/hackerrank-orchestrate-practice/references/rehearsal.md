# Rehearsal procedure

## Question selection

Start with the participant's entry point and one real output row. Ask how input becomes evidence, typed observations, a decision and a serialized output. Require the exact order where ties, dates or conflicting rules matter.

Then choose questions supported by the available code:

- Which constant changes this outcome? Where did its value come from?
- What did the model observe, and which fields does code trust?
- Which evidence was actually read before it was cited?
- What happens after malformed output, a timeout or an interrupted run?
- What alternative was rejected, and what measurement supports the rejection?
- Which rows changed after the last improvement? What was the noise floor?
- What does an offline replay guarantee, and what changes with a fresh provider call?
- How does the final usage report tie to the output being submitted?
- Which likely hidden-data cases remain weak?

## Answer review

Use decision, mechanism, evidence, alternative and limitation as prompts, not a fixed word count. Verify code locations and measurements before marking an answer supported. If a source is missing, mark that claim UNKNOWN.

## Transcript review

Look for actual decisions preceding implementation, specific constraints, errors, rejected proposals and checks. Separate log-format validity from quality of the reasoning. Neither transcript length nor keyword frequency establishes ownership.

Produce a small evidence table: claim, supporting artifact, verdict and correction. Preserve the historical transcript and make any new rehearsal a separate artifact.
