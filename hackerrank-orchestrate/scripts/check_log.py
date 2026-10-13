#!/usr/bin/env python3
"""Validate an Orchestrate log.txt against the starter repo's logging rules.

Checks, per entry (an entry starts at a line like "## [2026-09-12T10:00:00+05:30] Title"):
  - exactly one non-empty tool= line
  - tool= is not a placeholder, a generic label (AI, assistant, ...) or only a model name
  - tool= matches --expect-tool when given (case-insensitive)
  - per-turn entries have a non-empty "User Prompt" block
  - timestamps never go backwards (the log is append-only)
  - no apparent secrets (API keys, tokens, private keys)

Failure it prevents: a transcript log with missing, placeholder or model-name tool=
lines, empty prompt blocks or leaked secrets, which the starter contract calls invalid.

The format comes from an edition profile in ../assets/editions/ (default: sept-2026,
the September 2026 starter AGENTS.md section 5). Use --profile june-2026, or a path to
your own JSON copied from template.json, when your edition's format differs.
--list-profiles shows what ships. --entry-regex and --prompt-header still override the
profile. If no entries match, the script says which shipped profile does match, if any.

Exit code 0 when clean, 1 when any error is found, 2 on usage errors.
Standard library only.
"""

import argparse
import json
import os
import re
import stat
import sys
from datetime import datetime

PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "editions")
DEFAULT_PROFILE = "sept-2026"
# Built-in copy of sept-2026.json so the script still works if copied on its own.
BUILTIN_PROFILE = {
    "name": "sept-2026",
    "entry_regex": r"^##\s*\[(?P<ts>[^\]]+)\]\s*(?P<title>.*)$",
    "prompt_header": "User Prompt",
    "section_headers": ["Agent Response Summary:", "Actions:", "Context:"],
    "session_start_title_match": "session start",
    "tool_rule": {"key": "tool", "required_in": "all", "exactly_one": True, "harness_not_model": True},
    "required_turn_sections": [],
    "title_max_length": 80,
    "secret_scan": True,
}
DEFAULT_ENTRY_REGEX = BUILTIN_PROFILE["entry_regex"]
DEFAULT_PROMPT_HEADER = BUILTIN_PROFILE["prompt_header"]

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


def prompt_block_empty(body, header, section_headers):
    """True when the prompt header exists but nothing follows before the next header."""
    for i, (_, line) in enumerate(body):
        if line.strip().lower().startswith(header.lower()):
            for _, nxt in body[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                # The next section header ends the block.
                if s.lower() in section_headers:
                    return True
                return False
            return True
    return None  # header absent


def shipped_profiles():
    names = []
    if os.path.isdir(PROFILE_DIR):
        names = sorted(f[:-5] for f in os.listdir(PROFILE_DIR) if f.endswith(".json") and f != "template.json")
    return names


def profile_type_errors(prof):
    """Wrong JSON types in a profile would crash later or silently disable a check."""
    if not isinstance(prof, dict):
        return ["must be a JSON object"]
    errs = []
    unknown = sorted(set(prof) - set(BUILTIN_PROFILE) - {"description", "provenance", "provenance_source", "provenance_notes"})
    if unknown:  # a misspelled key would silently fall back to the default
        errs.append(f"unknown keys {unknown}")
    for key, default in BUILTIN_PROFILE.items():
        if key not in prof or key == "tool_rule":
            continue
        val = prof[key]
        if isinstance(default, list):
            ok = isinstance(val, list) and all(isinstance(x, str) for x in val)
        elif isinstance(default, bool):
            ok = isinstance(val, bool)
        elif isinstance(default, int):
            ok = isinstance(val, int) and not isinstance(val, bool)
        else:
            ok = isinstance(val, type(default))
        if not ok:
            errs.append(f"{key} must be {type(default).__name__}" + (" of strings" if isinstance(default, list) else ""))
    rule = prof.get("tool_rule", {})
    if not isinstance(rule, dict):
        errs.append("tool_rule must be an object")
    else:
        for key, default in BUILTIN_PROFILE["tool_rule"].items():
            if key in rule and not isinstance(rule[key], type(default)):
                errs.append(f"tool_rule.{key} must be {type(default).__name__}")
    return errs


def load_profile(name_or_path):
    """Load a profile by shipped name or by path. None means the default profile."""
    if name_or_path is None:
        name_or_path = DEFAULT_PROFILE
        path = os.path.join(PROFILE_DIR, DEFAULT_PROFILE + ".json")
        if not os.path.exists(path):
            return dict(BUILTIN_PROFILE)
    elif os.path.exists(name_or_path):
        path = name_or_path
    else:
        path = os.path.join(PROFILE_DIR, name_or_path + ".json")
        if not os.path.exists(path):
            raise ValueError(f"unknown profile {name_or_path!r}; shipped: {', '.join(shipped_profiles()) or 'none'}")
    with open(path, encoding="utf-8-sig") as fh:
        prof = json.load(fh)
    problems = profile_type_errors(prof)
    if problems:
        raise ValueError(f"profile {path}: " + "; ".join(problems))
    merged = dict(BUILTIN_PROFILE)
    merged.update(prof)
    merged["tool_rule"] = dict(BUILTIN_PROFILE["tool_rule"], **prof.get("tool_rule", {}))
    re.compile(merged["entry_regex"])
    if merged["tool_rule"]["required_in"] not in ("all", "turns", "none"):
        raise ValueError("tool_rule.required_in must be all, turns or none")
    return merged


def matching_profiles(lines, skip):
    found = []
    for name in shipped_profiles():
        if name == skip:
            continue
        try:
            prof = load_profile(name)
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        rx = re.compile(prof["entry_regex"])
        if any(rx.match(line) for line in lines):
            found.append(name)
    return found


def check(path, expect_tool, profile):
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
    except UnicodeDecodeError:
        return [f"{path}: not valid UTF-8"], [], 0
    errors, warnings = [], []
    if text.startswith("\ufeff"):
        warnings.append("file starts with a UTF-8 BOM")
        text = text[1:]
    lines = text.splitlines()
    if "\r\n" in text:
        warnings.append("file uses CRLF line endings; the starter asks for \\n")

    prompt_header = profile["prompt_header"]
    section_headers = {h.lower() for h in profile["section_headers"]}
    rule = profile["tool_rule"]
    key = re.escape(rule["key"])
    start_match = profile["session_start_title_match"].lower()

    entries = split_entries(lines, re.compile(profile["entry_regex"]))
    if not entries:
        errors.append("no log entries found (expected lines like '## [ISO-8601 TIMESTAMP] Title')")
        others = matching_profiles(lines, profile.get("name"))
        if others:
            warnings.append(f"this log matches shipped profile(s) {', '.join(others)}; try --profile {others[0]}")
        else:
            warnings.append("this log matches no shipped profile; copy assets/editions/template.json and fill it "
                            "from your AGENTS.md, then pass --profile PATH")
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

        is_session_start = start_match in e["title"].lower()
        needs_tool = rule["required_in"] == "all" or (rule["required_in"] == "turns" and not is_session_start)
        tool_lines = [(n, l.split("=", 1)[1]) for n, l in e["body"] if re.match(r"^\s*" + key + r"\s*=", l)]
        if needs_tool and not tool_lines:
            errors.append(f"{where}: missing {rule['key']}= line")
        elif rule["exactly_one"] and len(tool_lines) > 1:
            errors.append(f"{where}: {len(tool_lines)} {rule['key']}= lines; the rule asks for exactly one")
        if rule["harness_not_model"] or expect_tool:
            for n, value in tool_lines:
                problem = tool_problem(value, expect_tool)
                if problem:
                    errors.append(f"line {n}: {problem}")

        if not is_session_start:
            empty = prompt_block_empty(e["body"], prompt_header, section_headers)
            if empty is None:
                errors.append(f"{where}: per-turn entry has no '{prompt_header}' block")
            elif empty:
                errors.append(f"{where}: '{prompt_header}' block is empty")
            body_lower = {l.strip().lower() for _, l in e["body"]}
            for sec in profile["required_turn_sections"]:
                if sec.strip().lower() not in body_lower:
                    errors.append(f"{where}: per-turn entry has no '{sec}' section")
        if len(e["title"]) > profile["title_max_length"]:
            warnings.append(f"{where}: title longer than {profile['title_max_length']} characters")

    if profile["secret_scan"]:
        for lineno, line in enumerate(lines, 1):
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    errors.append(f"line {lineno}: possible secret ({name}); redact as [REDACTED]")
    return errors, warnings, len(entries)


def special_files(args):
    """Path arguments that are named pipes or sockets: reading one with no writer hangs."""
    found = []
    for v in vars(args).values():
        for x in v if isinstance(v, list) else [v]:
            try:
                if isinstance(x, str) and stat.S_ISFIFO(os.stat(x).st_mode) | stat.S_ISSOCK(os.stat(x).st_mode):
                    found.append(x)
            except (OSError, ValueError):
                pass
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", nargs="?", help="path to log.txt")
    ap.add_argument("--expect-tool", help='exact harness name every tool= line must equal, e.g. "Claude Code"')
    ap.add_argument("--profile", help=f"edition profile name or JSON path (default: {DEFAULT_PROFILE})")
    ap.add_argument("--list-profiles", action="store_true", help="list shipped edition profiles and exit")
    ap.add_argument("--entry-regex", help="override: regex for an entry header line, with named groups ts and title")
    ap.add_argument("--prompt-header", help="override: label that starts the verbatim prompt block in per-turn entries")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2

    if args.list_profiles:
        for name in shipped_profiles():
            with open(os.path.join(PROFILE_DIR, name + ".json"), encoding="utf-8") as fh:
                prof = json.load(fh)
            mark = " (default)" if name == DEFAULT_PROFILE else ""
            print(f"{name}{mark} [{prof.get('provenance', 'UNKNOWN')}]: {prof.get('description', '')}")
        return 0
    if not args.log:
        ap.error("the log path is required")
    try:
        profile = load_profile(args.profile)
        if args.entry_regex:
            re.compile(args.entry_regex)
            profile["entry_regex"] = args.entry_regex
        if args.prompt_header:
            profile["prompt_header"] = args.prompt_header
    except (ValueError, OSError, json.JSONDecodeError, re.error, RecursionError) as exc:  # deep nesting
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        errors, warnings, n = check(args.log, args.expect_tool, profile)
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
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
