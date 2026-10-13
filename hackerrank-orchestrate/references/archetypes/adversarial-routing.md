# Adversarial routing

Shape: route, act on or mute incoming messages and media, where some inputs are hostile (scams, impersonation, text that tries to instruct the system). Source: an August 2026 top-40 project with full design docs.

## Architecture that held up

- **Two-stage isolation for media.** The extraction call (describe image, transcribe audio) has no routing vocabulary. Its output is then fenced as data before the routing call, so injected text in an image arrives as a quoted description.
- **Ordered rule tiers:** safety overrides, then payment or action authority, then guards, then caps and floors, then the model's proposal as the default. **Caps beat floors,** with one documented guard that can escape a cap. An overridden floor is recorded as overridden, not lost.
- **Evidence is selected, never generated.** The model never writes an evidence id; a tiered ranking over the receiver's own history picks them from a shortlist, with ownership and strict-past invariants asserted.
- **Confidence computed in code** from named features. Report calibration; never optimize it.
- **Reason text from a clause grammar** with a register check (length bounds, one sentence, no identifiers). Violations fail the row instead of being truncated, because a silently trimmed reason is a wrong explanation.

## Guards that fit

- **Fence untrusted content** with an unguessable nonce. If attacker text contains the fence token, escape it and log an event with a hash, never the content.
- **A rule for text that addresses the router.** Perception sets a flag when content tries to direct the system, and a hard override fires whether or not the injected claim is true.
- **Never trust file extensions.** Detect format from magic bytes. In one corpus more than half the media had a wrong extension.
- **Explicit failure dispositions** (ABORT / DEGRADE / FAIL ROW) with distinct exit codes. Budget exhaustion is ordered: completed calls are cached, so a rerun pays only for the remainder.
- **Content-addressed cache shipped with the submission,** with an `assert-identical` gate that diffs two runs.

## Grounding tests

- **Threat-model test:** inject an instruction into a message and prove the rules that do not read message text cannot change.
- **Ablation:** remove each input a rule declares in its `reads` set; the rule must stop firing.

## Where rows are lost

- Boundary between "mute as scam" and "act with caution". The fix that worked was resolved definitions in the prompt, not a threshold tuned against 30 rows.
- The confidence column, the most volatile under re-derivation because it was a sum with no thresholding. Measure the noise floor before trusting a one-row change.
