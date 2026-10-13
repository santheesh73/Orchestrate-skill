# Per-call usage log

The usage report must describe the final full-dataset run, and it cannot be rebuilt after the fact. Have the solution append one JSON object per model call to a JSONL file (for example `evaluation/usage.jsonl`) from the first paid call.

```json
{"provider": "anthropic", "model": "<model id>", "request_id": "<input row id>",
 "input_tokens": 1234, "output_tokens": 210,
 "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
 "run_id": "<one id per full run>"}
```

- `provider`, `model`, `input_tokens`, `output_tokens` are required. The rest are optional.
- Take token counts from the provider's response usage fields; never estimate them.
- Use one `run_id` per full run and pass `--run-id` to the report script so it summarizes only the final run.
- Never log prompts, keys or secrets here.

Build the report (prices are per million tokens and change; take them from the provider's current pricing page):

```
python scripts/usage_report.py evaluation/usage.jsonl --run-id <id> \
  --price "<model id>=<input $/MTok>:<output $/MTok>" \
  --requests <number of input rows> --out code/evaluation/usage_report.md
```
