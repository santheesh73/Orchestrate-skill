#!/usr/bin/env python3
"""Flag code literals that also appear as values in the dataset (sample coupling).

Failure it prevents: rules keyed on an id, a string or a number combination copied
from the dataset. That is the dataset coupling the generalization policy forbids, and
it is the first thing an "did you overfit?" interview question exposes.

What it flags:
  - string literals in code that equal a dataset cell value and are at least
    --min-length characters long, or look like ids (letters and digits mixed, or a
    value from a column whose name ends in "id")
  - numeric tuples or lists in Python code (two or more numbers) whose numbers all
    occur together in one dataset row

What it ignores:
  - CSV header names
  - docstrings
  - literals that also appear in the --spec files (problem_statement.md, AGENTS.md):
    the contract sanctions those, for example allowed output values
  - anything listed in --allowlist (one literal per line, # starts a comment)

Python files are parsed with ast; .js/.ts/.go/.java/.rb files get a regex pass for
quoted strings. Exit 0 when clean, 1 on findings, 2 on usage errors, 3 when no source
file or no dataset value was examined (clean by default is not clean). Heuristic: a
finding is a question to answer, not proof of overfitting.

Example:
  python corpus_literals.py --data dataset/*.csv --code code/ \
      --spec problem_statement.md AGENTS.md --allowlist literal_allowlist.txt

Standard library only.
"""

import argparse
import ast
import csv
import glob
import io
import os
import re
import stat
import sys
import warnings

# A justification can exceed the csv module's 131072-character default field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}
REGEX_EXTS = {".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt", ".rb"}
STRING_RE = re.compile(r"""(?:"([^"\\\n]{2,})"|'([^'\\\n]{2,})')""")
ID_LIKE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9][A-Za-z0-9_\-.:]*$")


def read_utf8(path, encoding="utf-8"):
    try:
        with open(path, encoding=encoding, newline="") as fh:
            return fh.read()
    except UnicodeDecodeError:
        raise ValueError(f"{path} is not valid UTF-8") from None


def read_csv(path):
    try:
        rows = list(csv.reader(io.StringIO(read_utf8(path, "utf-8-sig"), newline=None)))
    except csv.Error as exc:  # e.g. a NUL byte on Python 3.9
        raise ValueError(f"{path} is not parseable as CSV: {exc}") from None
    return (rows[0], rows[1:]) if rows else ([], [])


def to_number(s):
    try:
        v = float(s.replace(",", "")) if s.strip() else None
    except ValueError:
        return None
    return v


def load_dataset(paths, min_length):
    values, headers, row_numbers = {}, set(), []
    for path in paths:
        header, rows = read_csv(path)
        headers.update(h.strip() for h in header)
        id_cols = {i for i, h in enumerate(header) if h.strip().lower().endswith("id")}
        for n, row in enumerate(rows, 2):
            nums = set()
            for i, cell in enumerate(row):
                v = cell.strip()
                if not v:
                    continue
                num = to_number(v)
                if num is not None:
                    nums.add(num)
                if i in id_cols or len(v) >= min_length or ID_LIKE.match(v):
                    values.setdefault(v, f"{os.path.basename(path)}:{n}")
            if len(nums) >= 2:
                row_numbers.append((nums, f"{os.path.basename(path)}:{n}"))
    return values, headers, row_numbers


def docstring_nodes(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def python_literals(path):
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        src = fh.read()
    try:
        with warnings.catch_warnings():  # invalid escapes in participant code must not hide the file
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
    except (SyntaxError, ValueError, RecursionError):  # ValueError: NUL byte on 3.9-3.11
        return [], []
    skip = docstring_nodes(tree)
    strings, tuples = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            strings.append((node.lineno, node.value))
        elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) >= 2:
            nums = []
            for e in node.elts:
                if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.USub) and isinstance(e.operand, ast.Constant):
                    e, sign = e.operand, -1
                else:
                    sign = 1
                if isinstance(e, ast.Constant) and isinstance(e.value, (int, float)) and not isinstance(e.value, bool):
                    nums.append(sign * float(e.value))
                else:
                    nums = None
                    break
            if nums:
                tuples.append((node.lineno, nums))
    return strings, tuples


def regex_literals(path):
    strings = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            for m in STRING_RE.finditer(line):
                strings.append((lineno, m.group(1) or m.group(2)))
    return strings, []


def walk(root):
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(filenames):
            p = os.path.join(dirpath, f)
            if os.path.isfile(p):  # skips dangling symlinks
                yield p, os.path.relpath(p, root)


def load_lines(path):
    out = set()
    for line in read_utf8(path).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out


def scan(data_paths, code_paths, spec_paths=(), allowlist=None, min_length=6, stats=None):
    """Return findings; stats, when given, receives "files" and "values" examined."""
    values, headers, row_numbers = load_dataset(data_paths, min_length)
    files = 0
    spec_text = ""
    for p in spec_paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            spec_text += fh.read() + "\n"
    allowed = load_lines(allowlist) if allowlist else set()
    findings = []
    for root in code_paths:
        for path, rel in walk(root):
            ext = os.path.splitext(path)[1]
            if ext == ".py":
                strings, tuples = python_literals(path)
            elif ext in REGEX_EXTS:
                strings, tuples = regex_literals(path)
            else:
                continue
            files += 1
            for lineno, s in strings:
                v = s.strip()
                if v in values and v not in headers and v not in allowed and v not in spec_text:
                    findings.append((rel, lineno, f"string {v!r} equals dataset value at {values[v]}"))
            for lineno, nums in tuples:
                key = ",".join(f"{n:g}" for n in nums)
                if key in allowed:
                    continue
                need = set(nums)
                if len(need) < 2:
                    continue
                for row_nums, where in row_numbers:
                    if need <= row_nums:
                        findings.append((rel, lineno, f"numbers ({key}) all occur in dataset row {where}"))
                        break
    if stats is not None:
        stats["files"], stats["values"] = files, len(values) + len(row_numbers)
    return findings


def bounded_int(low):
    """argparse type: a whole number of at least low (out-of-range values used to be accepted)."""
    def parse(text):
        try:
            n = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"expected a whole number, got {text!r}")
        if n < low:
            raise argparse.ArgumentTypeError(f"must be at least {low}, got {n}")
        return n
    return parse


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
    ap.add_argument("--data", nargs="+", required=True, help="dataset CSV files or globs")
    ap.add_argument("--code", nargs="+", required=True, help="source directories or files")
    ap.add_argument("--spec", nargs="*", default=[], help="contract files whose literals are allowed")
    ap.add_argument("--allowlist", help="file of allowed literals, one per line")
    ap.add_argument("--min-length", type=bounded_int(1), default=6, help="shortest non-id string to compare (default 6)")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2

    data = []
    for pattern in args.data:
        matched = sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else [])
        data += [p for p in matched if p.lower().endswith(".csv")]
    if not data:
        print("error: no dataset CSV files found", file=sys.stderr)
        return 2
    for p in args.code + args.spec + ([args.allowlist] if args.allowlist else []):
        if not os.path.exists(p):
            print(f"error: {p} does not exist", file=sys.stderr)
            return 2
    stats = {}
    try:
        findings = scan(data, args.code, args.spec, args.allowlist, args.min_length, stats)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for rel, lineno, msg in findings:
        print(f"FOUND {rel}:{lineno}: {msg}")
    print(f"{len(data)} dataset files, {len(findings)} coupled literals"
          + ("" if not findings else "; justify each from the spec or the domain, or allowlist it"))
    if findings:
        return 1
    if not stats["files"] or not stats["values"]:
        print(f"UNKNOWN {stats['files']} source files and {stats['values']} dataset values examined, so nothing was compared")
        return 3
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
