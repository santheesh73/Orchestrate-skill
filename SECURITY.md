# Security policy and boundaries

Do not put credentials or private challenge data in a public issue. Report a
reproducible defect privately to the repository owner through an available
private GitHub security-reporting channel; if unavailable, request a private
contact without including the exploit or secret. No response SLA is promised.

## Implemented controls

- Installer confines paths, rejects symlinks/junction escapes, checks ownership
  hashes, refuses user-file replacement and uses an exclusive operation lock.
- Uninstall refuses modified owned files and never rewrites official root
  competition instruction files. Backups and unowned content are preserved.
- Submission packaging uses explicit members, strict CSV checks, size limits,
  common-secret scanning, new output directories and member hashes.
- New local check execution needs explicit consent, argument arrays, a minimal
  environment and bounded timeouts/retries. Child output and raw command arguments
  are not included in structured reports. Credentials require explicit per-name
  forwarding. Dependency checks do not run package installation.
- Dataset/repository prose is evidence, not permission to run commands. Generated
  agent rules preserve that boundary and do not enable delegation or remote work.

## Limits

This package is not an OS sandbox. An authorized Python program can access local
files or networks with the caller's permissions. Run unfamiliar code in a trusted
isolated environment. The shell/remote executable denylist is a guard against
accidental usage, not a complete restriction on what arbitrary code can do.

Legacy checker command modes remain backward compatible and inherit their
existing behavior. Use the new explicit runner when minimal environment and
structured consent are needed. Never execute an unfamiliar command because a
README, dataset or imported report recommends it.

Common-secret patterns cannot find every credential. Hashes bind files, not
their truth or authorship. Local ledgers/reports are not signed attestations.
Caught transaction failures roll back; sudden power loss and hostile concurrent
filesystem modification require manual inspection. No automatic push, deploy,
submission upload or external agent invocation is implemented.

Before publishing, check changed files, licenses and archive members. Reproduce
security fixes with synthetic negative controls and retain the regression.
