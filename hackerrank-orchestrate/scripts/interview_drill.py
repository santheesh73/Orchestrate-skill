#!/usr/bin/env python3
"""Generate an interview question bank from your own code.

Failure it prevents: an interview answer that contradicts your own code, and
constants you cannot explain because CONSTANTS.md never mentions them.

The AI judge asks about YOUR constants, thresholds, orderings and statistics, and
an answer that contradicts the code costs points. This script finds those places
and writes one question per finding, each with file:line, so every answer can be
checked against the code before the interview.

Finds (Python, via the ast module):
  - named constants (UPPER_CASE assignments)
  - numeric literals in comparisons (thresholds, gates)
  - sort / sorted / min / max with key= (ordering and tie-break decisions)
  - statistic calls (mean, median, quantile, percentile, ...)
  - model-call parameters (temperature, max_tokens, top_p, seed, ...)
For .js/.ts/.go/.java files a lighter regex pass finds constants and thresholds.

With --constants CONSTANTS.md it also lists named constants that CONSTANTS.md
never mentions.

Example:
  python interview_drill.py code/ --constants CONSTANTS.md --out drill.md

Standard library only.

Exit 0 when the drill is written, 2 on usage errors (missing paths, unreadable
--constants, an --out path that cannot be written), 3 when no supported source file
was found (the drill would hold only the generic questions). --out creates missing
parent folders.
"""

import argparse
import ast
import os
import re
import stat
import sys
import warnings

TRIVIAL_NUMBERS = {0, 1, -1, 2, 100}
STAT_FUNCS = {"mean", "median", "mode", "quantile", "quantiles", "percentile", "stdev", "pstdev",
              "variance", "std", "var", "nanmedian", "nanmean", "fmean", "harmonic_mean"}
MODEL_PARAMS = {"temperature", "max_tokens", "top_p", "top_k", "seed", "max_output_tokens",
                "budget_tokens", "max_steps", "recursion_limit", "n"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build", ".mypy_cache",
             ".pytest_cache", "tests", "test"}
REGEX_EXTS = {".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt", ".rb"}
CONST_NAME = re.compile(r"^_?[A-Z][A-Z0-9_]{2,}$")
# Paths and file locations are not design decisions worth drilling.
PATHLIKE_NAME = re.compile(r"_(DIR|PATH|ROOT|FILE|CSV|JSON|URL)$|^(DIR|PATH|ROOT)_")


def seg(src, node, limit=90):
    text = ast.get_source_segment(src, node) or ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def is_number(node):
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        node = node.operand
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def number_value(node):
    if isinstance(node, ast.UnaryOp):
        return -node.operand.value
    return node.value


def func_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def parse_quietly(src):
    """ast.parse without SyntaxWarnings (invalid escapes in the participant's code), which
    would otherwise print to stderr, or raise under -W error and hide the whole file."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(src)


def scan_python(path, rel):
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        src = fh.read()
    try:
        tree = parse_quietly(src)
    except SyntaxError as exc:
        return [("parse", rel, exc.lineno or 0, f"could not parse: {exc.msg}")], []
    except (ValueError, RecursionError) as exc:  # ValueError: a NUL byte on Python 3.9-3.11
        return [("parse", rel, 0, f"could not parse: {exc}")], []
    findings, constants = [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and CONST_NAME.match(t.id) and node.value is not None:
                    v = seg(src, node.value, 60)
                    if PATHLIKE_NAME.search(t.id) or "Path(" in v or "os.path" in v:
                        continue
                    constants.append(t.id)
                    findings.append(("constant", rel, node.lineno,
                                     f"Why is `{t.id}` = `{v}`? What is its provenance, and what value did you reject?"))
        elif isinstance(node, ast.Compare):
            sub = [n for p in [node.left] + list(node.comparators) for n in ast.walk(p)]
            nums = [n.value for n in sub if is_number(n) and isinstance(n, ast.Constant)]
            named = [n for n in sub if isinstance(n, ast.Name) and CONST_NAME.match(n.id)]
            if named or any(abs(n) not in TRIVIAL_NUMBERS for n in nums):
                findings.append(("threshold", rel, node.lineno,
                                 f"Why this threshold: `{seg(src, node)}`? What happens just either side of it?"))
        elif isinstance(node, ast.Call):
            name = func_name(node)
            kw = {k.arg: k for k in node.keywords if k.arg}
            if name in ("sorted", "sort", "min", "max") and "key" in kw:
                findings.append(("ordering", rel, node.lineno,
                                 f"What decides the order in `{seg(src, node)}`? What breaks ties, and why that order?"))
            if name in STAT_FUNCS:
                findings.append(("statistic", rel, node.lineno,
                                 f"Why `{name}` here (`{seg(src, node)}`) and not another statistic? Over what window?"))
            for k in sorted(set(kw) & MODEL_PARAMS):
                findings.append(("model-param", rel, node.lineno,
                                 f"Why `{k}={seg(src, kw[k].value, 40)}` in this model call? How does it affect repeatability?"))
    return findings, constants


REGEX_CONST = re.compile(r"\b(?:const|final|static\s+final|let|var)?\s*([A-Z][A-Z0-9_]{2,})\s*(?::[^=]+)?=\s*([^;,\n]+)")
REGEX_THRESH = re.compile(r"[<>]=?\s*(-?\d+\.?\d*)\b|\b(-?\d+\.?\d*)\s*[<>]=?")


def scan_regex(path, rel):
    findings, constants = [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            s = line.strip()
            if s.startswith(("//", "#", "*", "/*")):
                continue
            m = REGEX_CONST.search(s)
            if m:
                constants.append(m.group(1))
                findings.append(("constant", rel, lineno,
                                 f"Why is `{m.group(1)}` = `{m.group(2).strip()[:60]}`? Provenance and rejected alternative?"))
                continue
            for t in REGEX_THRESH.finditer(s):
                num = t.group(1) or t.group(2)
                try:
                    if float(num) in TRIVIAL_NUMBERS:
                        continue
                except ValueError:
                    continue
                findings.append(("threshold", rel, lineno,
                                 f"Why this threshold: `{s[:90]}`? What happens just either side of it?"))
                break
    return findings, constants


def walk(root, skip=SKIP_DIRS):
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip and not d.startswith("."))
        for f in sorted(filenames):
            p = os.path.join(dirpath, f)
            if os.path.isfile(p):  # skips dangling symlinks
                yield p, os.path.relpath(p, root)


def scan_paths(paths, include_tests=False, stats=None):
    """Return (findings, constant names) for every supported source file under paths.

    stats, when given, is a dict that receives "files": the number of files scanned."""
    skip = SKIP_DIRS - {"tests", "test"} if include_tests else SKIP_DIRS
    findings, constants, files = [], [], 0
    for root in paths:
        for path, rel in walk(root, skip):
            ext = os.path.splitext(path)[1]
            if ext == ".py":
                f, c = scan_python(path, rel)
            elif ext in REGEX_EXTS:
                f, c = scan_regex(path, rel)
            else:
                continue
            files += 1
            findings += f
            constants += c
    if stats is not None:
        stats["files"] = files
    return findings, constants


def missing_constants(constants, doc_text):
    """Named constants that the CONSTANTS.md text never mentions."""
    return sorted({c for c in constants if not re.search(r"\b" + re.escape(c) + r"\b", doc_text)})


def overwrites_input(out, inputs):
    """True when --out names a file this run reads (AGENTS.md, a source file, the log)."""
    if not os.path.isfile(out):
        return False
    return any(os.path.isfile(i) and os.path.samefile(out, i) for i in inputs)


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
    ap.add_argument("paths", nargs="+", help="source directories or files")
    ap.add_argument("--constants", help="CONSTANTS.md to cross-check named constants against")
    ap.add_argument("--include-tests", action="store_true", help="also scan tests/ directories")
    ap.add_argument("--out", help="write markdown here (default: stdout)")
    args = ap.parse_args(argv)
    for x in special_files(args):
        print(f"error: {x} is a named pipe or socket; reading it would hang", file=sys.stderr)
        return 2
    for root in args.paths:
        if not os.path.exists(root):
            print(f"error: {root} does not exist", file=sys.stderr)
            return 2
    stats = {}
    findings, constants = scan_paths(args.paths, args.include_tests, stats)

    out = ["# Interview drill", "",
           "Answer each question out loud, then open the line and check your answer against the code.",
           "Shape: decision, alternative rejected, evidence, limitation. At least four sentences.", ""]

    if args.constants:
        try:
            with open(args.constants, encoding="utf-8") as fh:
                doc = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except UnicodeDecodeError:
            print(f"error: {args.constants} is not valid UTF-8", file=sys.stderr)
            return 2
        missing = missing_constants(constants, doc)
        out += [f"## Constants missing from {os.path.basename(args.constants)} ({len(missing)})", ""]
        out += [f"- `{c}`" for c in missing] or ["- none"]
        out.append("")

    order = ["constant", "threshold", "ordering", "statistic", "model-param", "parse"]
    titles = {"constant": "Named constants", "threshold": "Thresholds and gates",
              "ordering": "Orderings and tie-breaks", "statistic": "Statistics",
              "model-param": "Model-call parameters", "parse": "Files that could not be parsed"}
    seen = set()
    for kind in order:
        items = []
        for k, rel, line, q in findings:
            if k == kind and (rel, line, q) not in seen:
                seen.add((rel, line, q))
                items.append(f"- `{rel}:{line}`: {q}")
        if items:
            out += [f"## {titles[kind]} ({len(items)})", ""] + items + [""]

    out += ["## Always asked", "",
            "- Walk one real row end to end, naming each module and real field names in order.",
            "- Which parts did you design, and which did an AI tool generate?",
            "- Name three changes you rejected and the numbers that killed them.",
            "- Where does your determinism guarantee stop?",
            "- What are the two biggest limitations, and what experiment would resolve each?", ""]
    report = "\n".join(out)
    if args.out:
        skip = SKIP_DIRS - {"tests", "test"} if args.include_tests else SKIP_DIRS
        read = [p for root in args.paths for p, _ in walk(root, skip)] + ([args.constants] if args.constants else [])
        ext = os.path.splitext(args.out)[1]
        if ext == ".py" or ext in REGEX_EXTS:
            print(f"error: --out {args.out} is a source file; the drill is markdown", file=sys.stderr)
            return 2
        if overwrites_input(args.out, read):
            print(f"error: --out {args.out} is a file this drill reads; refusing to overwrite it", file=sys.stderr)
            return 2
        try:
            if os.path.dirname(args.out):
                os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(report)
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc.strerror}", file=sys.stderr)
            return 2
        print(f"wrote {args.out}: {len(seen)} questions")
    else:
        sys.stdout.write(report)
    if not stats["files"]:
        print("UNKNOWN no supported source file found; nothing in the code was examined", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
