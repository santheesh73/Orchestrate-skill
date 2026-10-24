# V4 verification and acceptance

This is a release candidate for maintainer review. The maintainer subsequently
authorized committing and pushing it to codex/hackathon-evidence. This is not a
tagged release. Baseline revision: 76c928eedce69fb62cc33a81c18349d37b14b53f.
The exact unchanged baseline was frozen before implementation and passed
262 tests in 479.045 seconds, with two platform-specific skips.

## Implemented scope

The candidate implements the nine component contracts in V4_ARCHITECTURE.md:
challenge intelligence, workflow policy, existing universal adapters plus owned
restore, evaluation V2, scoring, memory, mentor, interview intelligence and the
edition release/security gate. All original skills remain; the canonical entry
adds one on-demand coordinator row. Its activation description, all canonical
rules and original ten checker sources remain intact. The deliberate entrypoint
hash addition is recorded in integrations/upstreams.json.

## Verification results

| Check | Actual local result |
|---|---|
| Unchanged frozen baseline | 262 tests in 479.045 seconds; OK, two platform-specific skips |
| Initial focused V4 controls | 51 tests in 58.465 seconds; OK |
| Full regression before final relation hardening | 313 tests in 562.096 seconds; OK, two platform-specific skips |
| Final focused controls including counterfactual ID coverage | 51 tests in 58.804 seconds; OK |
| Original interfaces and installed-copy smoke | PASS; core and all companions validate |
| V4 demo | PASS; two actual trusted-fixture runs, independent saved replay, defect control, registry, mentor, interview, gate and package/handoff |
| Wheel/module distribution | PASS outside checkout; all six skills validate, all adapter install/doctor/uninstall checks pass, new commands run |
| Exercised documentation/distribution commands | 26 command checks PASS, including intentional UNKNOWN exits |
| Static syntax/security checks | 38 source files, zero errors; Python 3.9 grammar checked |
| Canonical source/content validation | PASS; unchanged trigger description, rules, original ten checkers and existing companions |
| Local documentation links | 97 links/anchors checked, zero errors |
| External HTTP destinations | 30 reachable, zero confirmed 404s, two UNKNOWN responses |
| Mermaid and mobile preview | Two accessible diagrams render; 390px viewport has no page-wide overflow |
| Original audit and behavior controls | PASS; separate from participant quality evidence |
| Offline lexical trigger proxy | 56 prompts; precision 0.76, recall 0.68; not live activation |

The canonical skill remains within the original budgets: always-loaded context
8,385 characters of 8,500; on-demand resources 199,960 of 200,000. Budgets were
not raised. The candidate's 105 source/test/resource fingerprints are recorded in
[the source manifest](v4-source-manifest.json), with LF-normalized aggregate
479d2dab643c03ee3be24326fd03a66b0a20f9ad17e2c0f9a2a0b4fec0fd0c67.

Final review tightened different_csv relations so changed row IDs cannot masquerade
as changed decisions. The final focused run verified that missing/replaced IDs fail
and genuine output changes on the same IDs pass. This narrow hardening followed
the full regression and distribution runs; no original validator was changed.

The own-only diagnostic measured four healthy/fifteen defective packaging fixtures
and five healthy/three defective decision-ID fixtures, with no false positives or
false negatives on those small known sets. These are not generalization estimates.
See [benchmark scope and raw evidence](V4_BENCHMARK.md).

## Acceptance limits

- Fresh external-reference runtime benchmarking is incomplete: automatic approval
  review rejected that execution because isolation and authorization were not
  established. Only own fixtures and pinned source observations are currently measured.
- Live coding-agent activation and effectiveness remain UNKNOWN. No new model
  inference, official hidden-data score or participant interview result is claimed.
- Supplied reproduction and manual-review records are not authenticated execution
  proofs. Local READY applies only to the configured local contract and reviews.
- Host Application Control has blocked generated console launchers; module and
  installed-content checks are distinct from console-executable verification.
- Remote V4 CI was unexecuted when these local results were recorded; consult
  the branch's Actions run for the published revision rather than inferring its result.
- Direct HTTP checking returned 403 for the historical Medium community article
  and 500 for the October event page; these destinations remain UNKNOWN in that
  check. Organizer content was available through the browser research tool; the
  historical community link and attribution have not been silently removed.

## Acceptance disposition

All nine components have working offline implementations and locally passing
tests. Existing functionality is preserved, local installation remains owned and
repeatable, release gating blocks missing/stale evidence, and documentation
matches the implemented interfaces. The candidate is ready for maintainer review.
Full comparative/live/cross-platform release verification is **incomplete** for the
specific reasons above. Branch publication was subsequently authorized; no model
call or external-reference execution was performed. The source manifest records
the precommit candidate snapshot, not a fabricated release revision.

The full V4 mission must not be labeled completely verified while these external
criteria remain unmeasured. There is no supported overall-superiority claim.
