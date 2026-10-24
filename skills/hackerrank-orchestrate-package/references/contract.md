# Submission contract

The synthetic asset must be adapted to the current statement. It is not an automatic specification extractor. Unknown or misspelled config keys fail.

## Fields

All source paths are exact paths relative to `--repo`. Directories, globs, absolute paths, traversal, control characters and symlinks are refused. A source must be a nonempty regular file. No source code is executed.

| Field | Meaning |
|---|---|
| input | Input CSV, with nonempty unique IDs. |
| output | Final generated CSV, with exact columns, unique IDs and complete input coverage. |
| id_column | Required in input and output; IDs remain strings. |
| columns | Nonempty ordered list of unique output column names. |
| enums | Optional mapping from output column to nonempty list of allowed strings. |
| allow_blank | Optional list of output fields the statement permits to be blank. IDs cannot be blank. |
| require_order | Required boolean; enforce input ordering only when the statement requires it. |
| code_files | Explicit, nonempty list of files placed at those relative paths in code.zip. |
| required_code_files | Required list, possibly empty; every member must appear in code_files. Include usage evidence here when required. |
| artifacts | Mapping from bundle-relative destination to repo-relative source. Must include the final CSV; can include transcript, README or other required artifacts. |
| hashes | Optional map from repo-relative source to expected SHA-256; use to bind the final code/output/usage run. |

Fill required artifact lists even when no extra file is required, so omission is a deliberate contract decision. The generated `manifest.json` records contract, input, output, archived members and copied artifact hashes. Record source hashes at the final run when provenance matters; a new manifest alone cannot prove that code generated an earlier CSV.

## Commands

```text
python scripts/package_submission.py --repo <project> --contract <contract.json> --out <new-package> --check-only
python scripts/package_submission.py --repo <project> --contract <contract.json> --out <new-package>
```

The script path is relative to this skill, independent of the project. A relative contract path is resolved from the calling directory, and a relative output directory is resolved beneath the project. The destination must be new, have an existing parent, and not overlap any input. No overwrite flag is provided.

CSV checks reject ragged records, duplicate headers/IDs, invalid UTF-8, NULs, missing rows, blank required fields and invalid enums. Empty input/output is UNKNOWN and exits 3. Other validation failures exit 1; configuration/path/I/O errors exit 2; successful checks or build exit 0. A failed build leaves no published output.

## Archive policy and limits

The allowlist excludes common credential files, keys, Git/environment/cache directories, installed skill directories and dataset paths from code.zip. Copy a dataset as a separate artifact only if explicitly required by the statement. Text is scanned for common secret patterns; this is a useful guard, not proof that no secret or personal data exists. Manually inspect the manifest and archive.

Limits: standard-library Python 3.9+, UTF-8 CSV, bounded file/field sizes, local filesystem. Cross-column business rules, transcript validity, model behavior and arbitrary secret formats require the existing checks and human review. Installation does not authorize submission or paid model calls.
