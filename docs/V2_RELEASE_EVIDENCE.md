# V2 first-increment release evidence

Version 3.1.0 preserves every existing skill and the original ten checker sources.
The mission asked for Sprint 1 immediately and the first verified improvement;
the rest of its six-sprint roadmap remains in V2_IMPLEMENTATION_PLAN.md.

## What changed and why

The independent comparison found useful existing packaging safeguards and a
benign literal flagged by the broader corpus scanner. A new opt-in decision_ids
policy inspects actual dataset IDs in Python comparisons, mapping keys and
lookups. Its built-in registry loads no participant plugin code. The preserved
scanner continues to support broader investigation. Existing CLI calls work
without the new config field.

`audit-selftest` makes audit quality reproducible using positive, injected-defect
and metamorphic controls for contract, replay and decision-ID audits. Tests
deliberately turn checkers into always-pass/always-fail implementations and
confirm the controls reject them. Reports include input and checker hashes. A
passing audit-selftest is deliberately not accepted as participant workflow
evidence.

The comparison records exact revisions, checker hashes, source dirtiness,
fixture fingerprints, process outcomes, per-category denominators, N/A policies,
UNKNOWN capabilities and one-run timings. Equal-interface and complete scenario
views are separate. See COMPETITIVE_BASELINE.md and the raw JSON reports.

## Validation record

Before implementation: 219 tests passed in 295.106 seconds with two
platform-specific skips. Competitor selftest passed its own ten injections and
three benign controls. After implementation, twelve focused test methods passed,
including every shared fixture, incomplete coverage, consent boundaries, source
bindings and evidence-kind separation. Static checks found no errors in the
new toolkit and benchmark sources.

The complete local regression run passed: **231 tests in 242.471 seconds, two
platform-specific skips**. Final focused registry/unsupported-source/installer
controls also passed. The first full run caught stale documentation counts and a
missing live count in the latest changelog; those were corrected and verified.
The original release smoke checks pass. Clean-wheel installation outside the
checkout passes, including audit-selftest and all adapter lifecycle operations.
The lexical trigger proxy remains precision 0.76, recall 0.68 on its existing
fixture set; it is not live activation evidence.

Final fixture review corrected stale output IDs in the cross-domain leakage
example. Every leakage fixture now also passes its base contract and produces
the expected result through the complete evaluation entrypoint. The focused
controls passed again, and both comparison reports were regenerated against
revision `8f75f602ec74463696cdb25537f8f8964dbdf331`; detection results were unchanged.

Remote execution of the pushed implementation is recorded in
[the nine-job Actions run](https://github.com/santheesh73/Orchestrate-skill/actions/runs/40064979317).
Its per-job conclusions are authoritative; documentation followups have their
own branch runs. The matrix runs the full suite, public selftest,
static/source validation, offline trigger proxy,
existing packaging smoke and clean-wheel checks on Windows/Linux/macOS with
Python 3.9, 3.11 and 3.13. No competitor code is fetched or executed by CI.

## Boundaries

This is a first verified improvement, not universal supremacy. Synthetic cases
are small, known and not blinded; no live agent was invoked. The new policy is
literal Python syntax analysis, not a dataflow/leakage proof. Existing execution
consent and host-permission boundaries still apply. No transcript, official score,
experiment result, hidden-label result or agent activation was manufactured.
