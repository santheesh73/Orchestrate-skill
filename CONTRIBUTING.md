# Contributing

Preserve existing skills, checker interfaces, competition instruction files and
the separation between current requirements and historical examples. Add focused
guidance only when it changes a decision; move conditional detail into references.

Before changing an adapter, open its official documentation, record the reviewed
date/source in the registry, and test installation, ownership, conflict handling,
activation-file format and removal. A simulated test must never become a live
runtime verification claim. Use isolated temporary projects and no paid APIs.

Development checks:

```text
python tools/validate_skill.py
python tools/package_addons.py --validate-only
python tools/static_check.py
python tools/check_docs.py
python tools/v4_demo.py
python tools/evaluate_behavior.py selftest --suite evals/behavior
python -m orchestrate_toolkit audit-selftest
python -W error -m unittest discover -s tests -v
python tools/ci_check.py
python tools/wheel_smoke.py
```

The wheel check needs pip, setuptools and wheel installed locally; its own build
and temporary install use --no-index. Source-tree runtime and unit tests use the
standard library. Use Python 3.9+ and keep Windows, Linux and macOS CI green.

Never commit credentials, generated installations, model-generated transcripts
presented as human history, or unlicensed copied prose. Include the upstream
notice when adapting licensed work. Add a regression that demonstrates a real
failure; avoid tests that merely assert headings or mirror implementation lines.

Use small commits. Record deliberate skill-contract changes in upstreams.json
without relaxing tests that protect original rules. Update current test counts
and render historical changelog counts as historical facts.

For built-in contract audits, add an explicit name to the closed registry and
provide healthy, injected-defect and unsupported-input controls. Prove the
selftest rejects a deliberately broken checker. Do not import participant code.
Comparisons must keep identical fixture bytes and requirements for both tools,
report UNKNOWN/N/A honestly and disclose heuristic differences. See
benchmarks/comparison/README.md. Do not tune an audit to hide a benchmark miss.

Behavior cases, protocol and run formats are documented in docs/BEHAVIOR_EVALUATION.md.
Preserve live/synthetic origin distinctions and missing semantic reviews. Never
include model-generated tool events as evidence of an actual invocation. Behavior
controls and source hashes test the grader; they do not certify agent effectiveness.

V4 schemas, component contracts and the candidate verification record live in
docs/V4_USAGE.md, docs/V4_ARCHITECTURE.md and docs/V4_VERIFICATION_REPORT.md. Keep
source-bound estimates honest about missing weight; preserve manual and execution
boundaries. Use the own-only synthetic benchmark when reference execution is not
authorized. Never treat a source-based capability comparison as a live measurement.
