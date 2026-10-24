---
name: hackerrank-orchestrate-package
description: Build a contract-driven HackerRank Orchestrate submission bundle with exact CSV coverage, explicit archive members, required-file checks and SHA-256 provenance. Use when final output is ready for packaging or submission-readiness checks. Do not use for packaging this skill itself, uploading a submission or general zip creation.
---

# Package a competition submission

Keep the current challenge statement authoritative. Read it and starter instructions, then fill `assets/submission-contract.json`; the example is synthetic, not an edition specification. Read `references/contract.md` for configuration and limitations.

## Workflow

Inputs: project, explicit contract and final artifacts. Outputs: a new bundle and manifest, or validation findings. On failure preserve inputs and prior bundles, fix the producer/configuration and retry after the failing check is resolved.

1. Confirm the final output came from the intended code/run. Complete existing preflight, selfcheck and human review. Record unresolved quality checks honestly.
2. Create the explicit contract from the current challenge. List the files to include in code.zip, required archive files, copied artifacts, CSV fields/enums and row-order requirement.
3. Run `scripts/package_submission.py --repo PROJECT --contract CONTRACT --out NEW_DIRECTORY --check-only` to validate inputs without writing.
4. Build with the same command without `--check-only`. The output directory must not exist. The script stages a new directory and records member hashes before publishing it.
5. Extract into a fresh location and follow only the README. Verify regenerated output matches the submitted artifact; review cross-column rules, evidence grounding, costs and authenticity separately.

## Hard rules

1. **Never repair CSV values by hand.** Fix the producer and regenerate the artifact.
2. **Require explicit packaging scope.** No inferred edition schema, recursive catch-all archive or automatic dataset inclusion.
3. **Preserve inputs and earlier packages.** Output collisions, symlinks, missing files and empty data fail before publication.
4. **State the verification boundary.** The script checks configured shape and files; it cannot establish hidden-label accuracy, correct contract transcription or full submission readiness.

## Completion evidence

Return the new directory, manifest and remaining human checks. The script prints PACKAGE BUILT, not an official readiness verdict. Uploading is a separate user-authorized action.
