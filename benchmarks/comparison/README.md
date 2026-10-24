# Independent synthetic comparison

These original fixtures exercise both repositories on the same artifact bytes
and declared requirements. No competitor code or prose is copied. Pin and review
its checkout before authorizing its scripts. The runner does not clone, install
dependencies, call models, execute fixture source or touch global skill folders.

```text
python benchmarks/comparison/run.py --report comparison-local.json
python benchmarks/comparison/run.py --competitor ../kit --allow-competitor-exec --report comparison-both.json
python benchmarks/comparison/run.py --competitor ../kit --allow-competitor-exec --own-leakage-audit decision_ids --report comparison-narrow-audit.json
```

Reports must be new files in existing directories. The default own leakage
adapter runs the preserved broad corpus scanner. `decision_ids` explicitly
selects the new narrower policy. Installation uses equivalent canonical skill
folder conflicts with mapped names; those paths cannot be byte-identical because
the projects' skill names differ. Only temporary directories are supplied.

`fixtures.json` is the oracle: `defect` labels are local synthetic expectations,
not HackerRank labels. Healthy cases include quoting, Unicode, CRLF, instruction
text in data, comments, docstrings, an isolated fixture assignment and an unseen
probe ID. Defects cover schema/coverage/order/enums/cells, malformed row width,
empty evidence, missing required artifacts, a synthetic credential pattern,
environment sidecars and literal-ID decisions in two naming domains.

Packaging is an acceptance/refusal test using equivalent schemas and enum flags.
The competitor has no CLI switch for mandatory usage reports or sidecar denial;
the shared statement still requires them. Their observed acceptance is reported,
but unsupported policies are N/A and excluded from that engine's error rates.
`common_interface_metrics` also excludes those scenarios for our engine so the
comparison uses identical denominators. This does not characterize every check
in the competitor's separate evaluator.
Normal documented refusal codes count as blocking; a crash, unavailable process,
oversized output or timeout is UNKNOWN, excluded from accuracy denominators.

Leakage metrics use a shared **no literal sample-ID decisions** policy. The
original corpus scanner is deliberately broader and emits investigation hints;
a hit counted as a false positive here does not mean its heuristic is broken.
Likewise the competitor's regex and our new AST policy have different coverage.
Neither can prove dataflow independence or generalization. Input IDs are read
from the actual fixture, including a different naming domain and an unseen ID.

Results include per-category FP/FN counts, denominators and rates, process exit
codes, output hashes, artifact fingerprints, checker/runner hashes, revision,
working-tree dirtiness and environment. No cross-category aggregate winner is
computed. One-run timings include startup and filesystem overhead; they are not
statistical performance results. File discovery counts SKILL files, not semantic
activation. Real agents and adversarial model behavior remain UNKNOWN. Dry-run
is N/A for the competitor's simple installer and unmeasured here for ours;
our existing lifecycle tests cover it independently.

The runner returns zero when it finishes writing a diagnostic, even if a checker
misses defects. It is **not a release gate**. Tests assert this repository's
expected narrow-audit results, and `audit-selftest` is the audit quality gate.
CI never downloads or executes the competitor. Use the checked-in Windows
reports as historical observations, not immutable claims about future revisions.
