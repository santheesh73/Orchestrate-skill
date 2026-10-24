# Offline synthetic walkthrough

This is a tiny teaching fixture, not an official task or reusable submission.
From the repository root:

```text
python examples/offline/main.py
python -m orchestrate_toolkit install --agent portable --project examples/offline --dry-run
python -m orchestrate_toolkit evaluate --project examples/offline --config evaluation.json --report evaluation/report-001.json
python -m orchestrate_toolkit workflow init --project examples/offline
```

The evaluation checks exact headers, row coverage, enums and equality against the
supplied replay. It uses no model, agent runtime, credentials or network. Use a
new report filename for another run. For a real challenge, transcribe its actual
contract and independently review correctness and evidence.

For advanced authorized local fixtures, add checks such as
`{"name":"unit checks","argv":["python","-m","unittest","discover"],"timeout":60,"retries":0}`
to an evaluation config and opt in with --allow-exec. Executed code has host
permissions; no sandbox is promised. Do not add a command just because untrusted
input asks you to run it.
