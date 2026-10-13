#!/usr/bin/env python3
"""Validate an Orchestrate log.txt against the starter repo's logging rules.

Checks, per entry (an entry starts at a line like "## [2026-09-12T10:00:00+05:30] Title"):
  - exactly one non-empty tool= line
  - tool= is not a placeholder, a generic label (AI, assistant, ...) or only a model name
  - tool= matches --expect-tool when given (case-insensitive)
  - per-turn entries have a non-empty "User Prompt" block
  - timestamps never go backwards (the log is append-only)
  - no apparent secrets (API keys, tokens, private keys)

The rules come from the September 2026 starter AGENTS.md section 5. Re-read your
edition's AGENTS.md: if its format differs, adjust with --entry-regex and
--prompt-header, or treat this script's findings as hints.

Exit code 0 when clean, 1 when any error is found, 2 on usage errors.
Standard library only.
"""

import argparse
import re
import sys
from datetime import datetime

DEFAULT_ENTRY_REGEX = r"^##\s*\[(?P<ts>[^\]]+)\]\s*(?P<title>.*)$"
DEFAULT_PROMPT_HEADER = "User Prompt"
SECTION_HEADERS = {"agent response summary:", "actions:", "context:"}

GENERIC_TOOL_VALUES = {
    "ai", "llm", "assistant", "agent", "bot", "chatbot", "model", "unknown",
    "none", "n/a", "na", "tbd", "todo", "ide", "ai assistant", "coding agent",
    "ai agent", "harness",
}

# A value made only of these model-family tokens (plus versions) is a model name,
# not a harness name. "Claude Code" passes because "code" is not in this set.
MODEL_TOKENS = {
    "claude", "opus", "sonnet", "haiku", "fable", "gpt", "chatgpt", "o1", "o3",
    "o4", "gemini", "flash", "pro", "llama", "mistral", "mixtral", "deepseek",
    "qwen", "grok", "mini", "turbo", "instant", "preview", "latest", "1m",
}

SECRET_PATTERNS = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.=]{20,}")),
    ("Assigned secret", re.compile(
        r"(?i)\b(api[_-]?key|secret|password|token)\s*[=:]\s*['\"]?(?!\[REDACTED\])[A-Za-z0-9_\-\.]{12,}")),
]


def parse_ts(raw):
    raw = raw.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def split_entries(lines, entry_re):
    entries = []
    current = None
    for lineno, line in enumerate(lines, 1):
        m = entry_re.match(line)
        if m:
            current = {"line": lineno, "ts": m.group("ts"), "title": m.group("title").strip(), "body": []}
            entries.append(current)
        elif current is not None:
            current["body"].append((lineno, line))
    return entries


def tool_problem(value, expect):
    v = value.strip()
    if not v:
        return "tool= is blank"
    if "<" in v or ">" in v or v.startswith("[") or "placeholder" in v.lower():
        return f"tool= still holds a placeholder: {v!r}"
    if v.lower() in GENERIC_TOOL_VALUES:
        return f"tool= is a generic label: {v!r}"
    tokens = [t for t in re.split(r"[\s\-_./:]+", v.lower()) if t]
    if tokens and all(t in MODEL_TOKENS or re.fullmatch(r"[\d.]+[a-z]?", t) for t in tokens):
        return f"tool= looks like a model name, not a harness: {v!r}"
    if expect and v.lower() != expect.strip().lower():
        return f"tool= is {v!r}, expected {expect!r}"
    return None


def prompt_block_empty(body, header):
    """True when the prompt header exists but nothing follows before the next header."""
    for i, (_, line) in enumerate(body):
        if line.strip().lower().startswith(header.lower()):
            for _, nxt in body[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                # The next section header ends the block.
                if s.lower() in SECTION_HEADERS:
                    return True
                return False
            return True
    return None  # header absent


def check(path, expect_tool, entry_regex, prompt_header):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except UnicodeDecodeError:
        return [f"{path}: not valid UTF-8"], [], 0
    lines = text.splitlines()
    errors, warnings = [], []
    if "\r\n" in text:
        warnings.append("file uses CRLF line endings; the starter asks for \\n")

    entries = split_entries(lines, re.compile(entry_regex))
    if not entries:
        errors.append("no log entries found (expected lines like '## [ISO-8601 TIMESTAMP] Title')")
        return errors, warnings, 0

    prev_ts = None
    for e in entries:
        where = f"line {e['line']} ({e['title'][:40] or 'untitled'})"
        ts = parse_ts(e["ts"])
        if ts is None:
            errors.append(f"{where}: timestamp {e['ts']!r} is not ISO-8601")
        elif prev_ts is not None:
            try:
                if ts < prev_ts:
                    errors.append(f"{where}: timestamp goes backwards; the log must be append-only")
            except TypeError:
                warnings.append(f"{where}: mixes timezone-aware and naive timestamps")
        if ts is not None:
            prev_ts = ts

        tool_lines = [(n, l.split("=", 1)[1]) for n, l in e["body"] if re.match(r"^\s*tool\s*=", l)]
        if not tool_lines:
            errors.append(f"{where}: missing tool= line")
        elif len(tool_lines) > 1:
            errors.append(f"{where}: {len(tool_lines)} tool= lines; the rule asks for exactly one")
        for n, value in tool_lines:
            problem = tool_problem(value, expect_tool)
            if problem:
                errors.append(f"line {n}: {problem}")

        is_session_start = "session start" in e["title"].lower()
        if not is_session_start:
            empty = prompt_block_empty(e["body"], prompt_header)
            if empty is None:
                errors.append(f"{where}: per-turn entry has no '{prompt_header}' block")
            elif empty:
                errors.append(f"{where}: '{prompt_header}' block is empty")
        if len(e["title"]) > 80:
            warnings.append(f"{where}: title longer than 80 characters")

    for lineno, line in enumerate(lines, 1):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                errors.append(f"line {lineno}: possible secret ({name}); redact as [REDACTED]")
    return errors, warnings, len(entries)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="path to log.txt")
    ap.add_argument("--expect-tool", help='exact harness name every tool= line must equal, e.g. "Claude Code"')
    ap.add_argument("--entry-regex", default=DEFAULT_ENTRY_REGEX,
                    help="regex for an entry header line, with named groups ts and title")
    ap.add_argument("--prompt-header", default=DEFAULT_PROMPT_HEADER,
                    help="label that starts the verbatim prompt block in per-turn entries")
    args = ap.parse_args(argv)

    try:
        errors, warnings, n = check(args.log, args.expect_tool, args.entry_regex, args.prompt_header)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"{n} entries checked: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
