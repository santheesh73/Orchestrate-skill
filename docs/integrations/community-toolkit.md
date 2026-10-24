# Additive companion skills and optional toolkit

The existing `hackerrank-orchestrate/SKILL.md`, its name, original checker scripts
and installation command remain in place. Four new independently implemented
skills live under `skills/`; each packages and runs without its siblings.

| Companion | Added capability |
|---|---|
| hackerrank-orchestrate-design | Adaptable design template and architecture review |
| hackerrank-orchestrate-package | Explicit-contract submission builder with member hashes |
| hackerrank-orchestrate-practice | Source-grounded interview rehearsal and transcript review |
| hackerrank-orchestrate-toolkit | Optional community CLI, memory and heuristic score review |

## Selection

Use the original skill to manage the event. Choose the design companion for a
written design, package for submission artifacts, practice for rehearsal, and
toolkit for that CLI specifically. Their descriptions distinguish these tasks
from general Orchestrate advice. Real automatic multi-skill routing is not yet
measured; invoke the requested companion explicitly if selection is ambiguous.

## Preservation and conflict policy

No original skill or checker is removed. Companion installation refuses existing
destinations and never installs the upstream collection in bulk. The current
challenge contract overrides historical examples. Existing project evaluation
policy governs conflicting regression/noise guidance; a demonstrated contract
violation remains a defect even when only one row exposes it. Respect whether
the user requested a prompt, a review or direct implementation.

The original skill is standard-library Python 3.9+. The optional toolkit requires
a separate Python 3.10+ environment. Its Orchestrate evaluator is specialized for
the message-router schema and cannot replace edition-specific preflight. Scores
and simulator feedback are heuristics; keep missing evidence UNKNOWN.

## Upstream tracking

See `integrations/upstreams.json` for reviewed revisions and imported-file policy,
and `THIRD_PARTY_NOTICES.md` for licenses and attribution. The toolkit companion's
reference includes pinned installation and command mapping. No external package
is installed as part of installing the skills, and no paid checks run in CI.

To refresh: inspect the upstream diff, review license/provenance and command
changes, run targeted negative controls, then update the pin and verification
date. Do not copy whole upstream skills or personal performance claims.

## Packaging boundary

The competition packager takes an explicit contract and allowlist, handles empty
data as UNKNOWN, checks required archive members, refuses overwrites/symlinks,
builds a new directory and records source/member hashes. It does not run target
code or claim official submission readiness. The participant must still verify
contract transcription, clean-run reproducibility, cross-column rules, evidence
grounding, transcript authenticity and final-run usage provenance.

Skill archives are built by the original `tools/package_skill.py` or the additive
`tools/package_addons.py`; these are separate from competition code.zip creation.
See `docs/INSTALL.md` for install commands.
