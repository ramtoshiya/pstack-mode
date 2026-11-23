#!/usr/bin/env python3
"""Decide whether the no-comments scope holds anything for Comment Sicko to review.

Scans the whole current content of every scoped file for comments, docstrings,
lint or type suppressions, and disabled code. Exit 0: none in any file, skip
Comment Sicko. Exit 1: found one, or a file could not be classified, run it.
Exit 2: the scope could not be resolved, run it.
"""

import argparse
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tokenize
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

CLEAN, COMMENT, SUPPRESSION, UNCLASSIFIED = "clean", "comment", "suppression", "unclassified"


class Unclassified(Exception):
    pass


class ScopeError(Exception):
    pass


class Hit(NamedTuple):
    line: int
    detail: str


class Scope(NamedTuple):
    description: str
    files: List[Tuple[str, Callable[[], Optional[bytes]]]]


class Verdict(NamedTuple):
    path: str
    kind: str
    line: Optional[int]
    detail: str


@dataclass(frozen=True)
class Quote:
    open: str
    close: str
    escape: bool = True
    multiline: bool = False


@dataclass(frozen=True)
class Syntax:
    line: Tuple[str, ...] = ()
    block: Tuple[str, ...] = ()
    quotes: Tuple[Quote, ...] = ()
    char_literal: Optional[str] = None
    line_after: Optional[str] = None
    quote_after: Optional[str] = None
    regex_literals: bool = False
    backslash: bool = False


CHAR = r"'(?:\\[^\n]{1,10}?|[^'\\\n])'"
DQ = Quote('"', '"')
SQ = Quote("'", "'")
C_STYLE = {"line": ("//",), "block": ("/*",)}
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {
    "", "return", "typeof", "case", "do", "else", "in", "of", "new", "delete",
    "void", "throw", "instanceof", "yield", "await",
}
WORD = re.compile(r"[A-Za-z0-9_$]+")

SYNTAXES = {
    "javascript": Syntax(**C_STYLE, quotes=(DQ, SQ, Quote("`", "`", multiline=True)), regex_literals=True),
    "json": Syntax(**C_STYLE, quotes=(DQ, SQ)),
    "css": Syntax(block=("/*",), quotes=(DQ, SQ)),
    "scss": Syntax(**C_STYLE, quotes=(DQ, SQ)),
    "c": Syntax(**C_STYLE, char_literal=CHAR, quotes=(
        Quote(r'(?:u8|[uUL])?R"([^()\\\s]{0,16})\(', r')\1"', escape=False, multiline=True), DQ)),
    "java": Syntax(**C_STYLE, char_literal=CHAR, quotes=(Quote('"""', '"""', multiline=True), DQ)),
    "kotlin": Syntax(**C_STYLE, char_literal=CHAR, quotes=(Quote('"""', '"""', escape=False, multiline=True), DQ)),
    "go": Syntax(**C_STYLE, char_literal=CHAR, quotes=(Quote("`", "`", escape=False, multiline=True), DQ)),
    "rust": Syntax(**C_STYLE, char_literal="b?" + CHAR, quotes=(
        Quote(r'b?r(#*)"', r'"\1', escape=False, multiline=True), Quote('b?"', '"', multiline=True))),
    "swift": Syntax(**C_STYLE, quotes=(
        Quote('(#*)"""', r'"""\1', multiline=True), Quote('(#+)"', r'"\1'), DQ)),
    "csharp": Syntax(**C_STYLE, char_literal=CHAR, quotes=(
        Quote('[$]*"""', '"""', escape=False, multiline=True),
        Quote(r'\$?@\$?"', '"', escape=False, multiline=True), Quote(r'\$?"', '"'))),
    "shell": Syntax(line=("#",), line_after=" \t\n;|&()", backslash=True, quotes=(
        Quote("'", "'", escape=False, multiline=True), Quote('"', '"', multiline=True),
        Quote("`", "`", multiline=True))),
    "yaml": Syntax(line=("#",), line_after=" \t\n", quote_after=" \t\n[{,", quotes=(
        Quote("'", "'", escape=False, multiline=True), Quote('"', '"', multiline=True))),
    "toml": Syntax(line=("#",), quotes=(
        Quote('"""', '"""', multiline=True), Quote("'''", "'''", escape=False, multiline=True),
        DQ, Quote("'", "'", escape=False))),
    "sql": Syntax(line=("--",), block=("/*",), quotes=(
        Quote("'", "'", escape=False, multiline=True), Quote('"', '"', escape=False, multiline=True))),
    "makefile": Syntax(line=("#",)),
    "hash-lines": Syntax(line=("#",), line_after=" \t\n"),
}

EXTENSIONS = {
    **dict.fromkeys((".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx"), "javascript"),
    **dict.fromkeys((".json", ".jsonc", ".json5"), "json"),
    ".css": "css", ".scss": "scss", ".less": "scss",
    **dict.fromkeys((".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx", ".m", ".mm"), "c"),
    ".java": "java", ".scala": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".go": "go", ".rs": "rust", ".swift": "swift", ".cs": "csharp",
    ".py": "python", ".pyi": "python",
    **dict.fromkeys((".sh", ".bash", ".zsh", ".bats", ".dockerfile"), "shell"),
    ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".sql": "sql", ".mk": "makefile",
    ".md": "markdown", ".markdown": "markdown",
    **dict.fromkeys((".html", ".htm", ".xhtml", ".xml", ".svg", ".vue", ".svelte"), "html"),
}
FILENAMES = {
    "Makefile": "makefile", "GNUmakefile": "makefile", "makefile": "makefile",
    "Dockerfile": "shell", "Containerfile": "shell",
    **dict.fromkeys((".gitignore", ".dockerignore", ".npmignore", ".prettierignore",
                     ".eslintignore", ".gitattributes", "CODEOWNERS"), "hash-lines"),
}
SHEBANGS = (("python", "python"), ("node", "javascript"), ("deno", "javascript"), ("bun", "javascript"),
            ("bash", "shell"), ("zsh", "shell"), ("sh", "shell"))
FENCE_LANGUAGES = {
    **dict.fromkeys(("js", "javascript", "jsx", "ts", "typescript", "tsx", "mjs"), "javascript"),
    **dict.fromkeys(("json", "jsonc", "json5"), "json"),
    "css": "css", "scss": "scss", "less": "scss",
    **dict.fromkeys(("c", "h", "cpp", "c++", "objc", "objective-c"), "c"),
    "java": "java", "scala": "java", "kotlin": "kotlin", "kt": "kotlin", "go": "go", "golang": "go",
    "rust": "rust", "rs": "rust", "swift": "swift", "csharp": "csharp", "cs": "csharp", "c#": "csharp",
    "python": "python", "py": "python",
    **dict.fromkeys(("sh", "bash", "shell", "zsh", "console", "shell-session", "dockerfile"), "shell"),
    "yaml": "yaml", "yml": "yaml", "toml": "toml", "sql": "sql", "make": "makefile", "makefile": "makefile",
    **dict.fromkeys(("html", "xml", "svg", "vue", "svelte"), "html"),
    **dict.fromkeys(("md", "markdown"), "markdown"),
}
COMMENT_MARKERS = ("#", "//", "/*", "(*", "<!--", "--", ";", "%")

SUPPRESSIONS = re.compile("|".join((
    r"eslint-(?:disable|enable)", r"@ts-(?:ignore|expect-error|nocheck)", r"\bnoqa\b",
    r"type:\s*ignore", r"pyright:\s*ignore", r"pylint:\s*disable", r"mypy:\s*ignore",
    r"\bnolint\b", r"\bNOLINT", r"rubocop:\s*disable", r"biome-ignore", r"prettier-ignore",
    r"\b(?:istanbul|c8|v8)\s+ignore", r"swiftlint:disable", r"shellcheck\s+disable",
    r"#!?\[(?:allow|expect)\(", r"@Suppress", r"SuppressMessage", r"\bnosec\b", r"nosemgrep",
    r"#\s*pragma\s+(?:warning|clang\s+diagnostic|GCC\s+diagnostic)", r"#\s*if\s+0\b",
    r"(?:stylelint|markdownlint|oxlint)-disable", r"tslint:disable", r"deno-lint-ignore",
    r"phpcs:ignore", r"@phpstan-ignore", r"@psalm-suppress", r"ktlint-disable",
)))


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def close_quote(text, start, close, quote):
    index = start
    while index < len(text):
        if quote.escape and text[index] == "\\":
            index += 2
        elif text.startswith(close, index):
            return index + len(close)
        elif text[index] == "\n" and not quote.multiline:
            break
        else:
            index += 1
    raise Unclassified(f"string at line {line_of(text, start)} does not close where expected")


def refuse_multiline_string_with_marker(text, start, end, markers):
    body = text[start:end]
    if "\n" in body and any(marker in body for marker in markers):
        raise Unclassified(f"multi-line string at line {line_of(text, start)} contains a comment marker, "
                           "so a misread quote may hide a comment")


def skip_regex_literal(text, start):
    index, in_class = start + 1, False
    while index < len(text) and text[index] != "\n":
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "/":
            flags = WORD.match(text, index + 1)
            return flags.end() if flags else index + 1
        index += 1
    raise Unclassified(f"regular expression at line {line_of(text, start)} does not close on its line")


def scan_syntax(syntax, text):
    quotes = [(re.compile(quote.open), quote) for quote in syntax.quotes]
    char_literal = re.compile(syntax.char_literal) if syntax.char_literal else None
    markers = syntax.line + syntax.block
    index, previous = len(text.split("\n", 1)[0]) if text.startswith("#!") else 0, ""
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if syntax.backslash and char == "\\":
            index, previous = index + 2, "x"
            continue
        boundary = index == 0 or syntax.line_after is None or text[index - 1] in syntax.line_after
        if (boundary and text.startswith(syntax.line, index)) or text.startswith(syntax.block, index):
            return Hit(line_of(text, index), "comment")
        match = char_literal.match(text, index) if char_literal else None
        if match:
            index, previous = match.end(), "x"
            continue
        if syntax.quote_after is None or index == 0 or text[index - 1] in syntax.quote_after:
            for pattern, quote in quotes:
                match = pattern.match(text, index)
                if match:
                    end = close_quote(text, match.end(), match.expand(quote.close), quote)
                    refuse_multiline_string_with_marker(text, match.end(), end, markers)
                    index, previous = end, "x"
                    break
            else:
                match = None
            if match:
                continue
        if syntax.regex_literals:
            if text.startswith(("</", "++", "--"), index):
                index, previous = index + 2, text[index:index + 2]
                continue
            if char == "/" and previous in REGEX_BEFORE:
                index, previous = skip_regex_literal(text, index), "x"
                continue
        match = WORD.match(text, index)
        if match:
            index, previous = match.end(), match.group()
        else:
            index, previous = index + 1, char
    return None


def scan_python(text):
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError) as error:
        raise Unclassified(f"Python does not tokenize: {error}") from None
    skipped = {tokenize.NL, tokenize.COMMENT, tokenize.STRING}
    statement_start = True
    for position, token in enumerate(tokens):
        if token.type == tokenize.COMMENT:
            if token.start != (1, 0) or not token.string.startswith("#!"):
                return Hit(token.start[0], "comment")
            continue
        if token.type == tokenize.NL:
            continue
        if token.type == tokenize.STRING and statement_start:
            following = next(t for t in tokens[position + 1:] if t.type not in skipped)
            if following.type in (tokenize.NEWLINE, tokenize.ENDMARKER):
                return Hit(token.start[0], "docstring")
        statement_start = token.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)
    return None


def scan_unlabeled(text):
    for marker in COMMENT_MARKERS:
        if marker in text:
            raise Unclassified(f"code in an unknown language contains {marker!r}")
    return None


def scan_embedded(language, text, first_line):
    try:
        hit = SCANNERS[language](text) if language else scan_unlabeled(text)
    except Unclassified as error:
        raise Unclassified(f"code at line {first_line}: {error}") from None
    return Hit(hit.line + first_line - 1, hit.detail) if hit else None


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})[ \t]*([^\s`{]*)")


def scan_markdown(text):
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        fence = FENCE.match(line)
        if fence:
            marker, info = fence.group(1), fence.group(2).lower()
            end = index + 1
            while end < len(lines) and not re.match(
                    r" {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$", lines[end]):
                end += 1
            hit = scan_embedded(FENCE_LANGUAGES.get(info), "\n".join(lines[index + 1:end]), index + 2)
            if hit:
                return hit
            index = end + 1
            continue
        if "<!--" in line:
            return Hit(index + 1, "comment")
        if line.startswith(("    ", "\t")) and any(marker in line for marker in COMMENT_MARKERS[:5]):
            raise Unclassified(f"indented code at line {index + 1} may hold a comment")
        index += 1
    return None


EMBEDDED = re.compile(r"<(script|style)\b([^>]*)>(.*?)</\1\s*>", re.I | re.S)


def scan_html(text):
    for match in EMBEDDED.finditer(text):
        tag, attributes = match.group(1).lower(), match.group(2).lower()
        if tag == "style":
            language = "scss" if re.search(r"lang=[\"']?(scss|less)", attributes) else "css"
        elif "json" in attributes:
            language = "json"
        elif re.search(r"type=[\"']?(?!module|text/javascript|application/javascript)", attributes):
            language = None
        else:
            language = "javascript"
        hit = scan_embedded(language, match.group(3), line_of(text, match.start(3)))
        if hit:
            return hit
    outside = EMBEDDED.sub(lambda match: "\n" * match.group().count("\n"), text)
    if re.search(r"<(script|style)\b", outside, re.I):
        raise Unclassified("a script or style element does not close")
    if "<!--" in outside:
        return Hit(line_of(outside, outside.index("<!--")), "comment")
    return None


SCANNERS: Dict[str, Callable[[str], Optional[Hit]]] = {
    **{name: (lambda syntax: lambda text: scan_syntax(syntax, text))(syntax)
       for name, syntax in SYNTAXES.items()},
    "python": scan_python, "markdown": scan_markdown, "html": scan_html,
}


def language_of(path, text):
    name = os.path.basename(path)
    if name in FILENAMES:
        return FILENAMES[name]
    if name.startswith(("Dockerfile.", "Containerfile.")):
        return "shell"
    suffix = os.path.splitext(name)[1].lower()
    if suffix:
        return EXTENSIONS.get(suffix)
    first = text.split("\n", 1)[0]
    if first.startswith("#!"):
        for program, language in SHEBANGS:
            if re.search(r"[/ ]" + program + r"[0-9.]*\b", first):
                return language
    return None


def classify(path, data):
    if data is None:
        return Verdict(path, CLEAN, None, "symlink")
    if b"\0" in data[:8000]:
        return Verdict(path, CLEAN, None, "binary")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return Verdict(path, UNCLASSIFIED, None, "not UTF-8 text")
    suppression = SUPPRESSIONS.search(text)
    if suppression:
        return Verdict(path, SUPPRESSION, line_of(text, suppression.start()), suppression.group())
    language = language_of(path, text)
    if language is None:
        return Verdict(path, UNCLASSIFIED, None, "no known comment syntax for this file type")
    try:
        hit = SCANNERS[language](text)
    except Unclassified as error:
        return Verdict(path, UNCLASSIFIED, None, f"{language}: {error}")
    if hit:
        return Verdict(path, COMMENT, hit.line, f"{language} {hit.detail}")
    return Verdict(path, CLEAN, None, language)


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, check=False)
    if result.returncode:
        raise ScopeError(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def names(output):
    return [name for name in output.decode().split("\0") if name]


def read_worktree(top, name):
    path = Path(top) / name
    if path.is_symlink():
        return None
    if path.is_dir():
        raise Unclassified("a directory or submodule")
    return path.read_bytes()


def resolve_scope(args) -> Scope:
    if not (args.staged or args.unstaged or args.base) and args.paths:
        files = []
        for given in args.paths:
            path = Path(given)
            if path.is_dir():
                listed = names(git("-C", given, "ls-files", "-z", "-co", "--exclude-standard"))
                files += [(os.path.join(given, name), read_worktree, ".") for name in listed]
            elif path.exists() or path.is_symlink():
                files.append((given, read_worktree, "."))
            else:
                raise ScopeError(f"{given} does not exist")
        return Scope("the given files", [(name, lambda n=name, r=reader, t=top: r(t, n)) for name, reader, top in files])
    top = git("rev-parse", "--show-toplevel").decode().strip()
    pathspec = ["--", *args.paths] if args.paths else []
    untracked = ["ls-files", "-z", "-o", "--exclude-standard", "--full-name", *pathspec]
    diff = ["diff", "--name-only", "-z", "--no-renames", "--diff-filter=d"]
    if args.staged:
        description = "staged changes"
        changed = names(git(*diff, "--cached", *pathspec))
        return Scope(description, [(name, lambda n=name: git("cat-file", "blob", f":{n}")) for name in changed])
    if args.unstaged:
        description = "unstaged changes and untracked files"
        changed = names(git(*diff, *pathspec)) + names(git(*untracked))
    else:
        base = args.base or "main"
        merge_base = git("merge-base", base, "HEAD").decode().strip()
        description = f"changes from {base} (merge base {merge_base[:12]}), with the working tree"
        changed = names(git(*diff, merge_base, *pathspec)) + names(git(*untracked))
    return Scope(description, [(name, lambda n=name: read_worktree(top, n)) for name in sorted(set(changed))])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--base", metavar="REF", help="scope is the diff from REF's merge base to the working tree (default: main)")
    mode.add_argument("--staged", action="store_true", help="scope is the staged diff, read from the index")
    mode.add_argument("--unstaged", action="store_true", help="scope is the unstaged diff and untracked files")
    parser.add_argument("paths", nargs="*", help="files to scan, or with a diff option, paths that limit the diff")
    args = parser.parse_args()
    try:
        scope = resolve_scope(args)
    except ScopeError as error:
        print(f"no-comments pre-check: cannot resolve the scope: {error}\nResult: run Comment Sicko.")
        return 2
    verdicts = []
    for name, read in scope.files:
        try:
            verdicts.append(classify(name, read()))
        except (OSError, ScopeError, Unclassified) as error:
            verdicts.append(Verdict(name, UNCLASSIFIED, None, str(error)))
    print(f"no-comments pre-check: {len(verdicts)} scoped files from {scope.description}")
    for verdict in verdicts:
        where = f"{verdict.path}:{verdict.line}" if verdict.line else verdict.path
        print(f"{verdict.kind:<13} {where}  ({verdict.detail})")
    flagged = [verdict for verdict in verdicts if verdict.kind != CLEAN]
    if not flagged:
        print(f"Result: no comments, docstrings, or suppressions in {len(verdicts)} scoped files. Skip Comment Sicko.")
        return 0
    counts = ", ".join(f"{sum(v.kind == kind for v in flagged)} {kind}"
                       for kind in (COMMENT, SUPPRESSION, UNCLASSIFIED) if any(v.kind == kind for v in flagged))
    print(f"Result: run Comment Sicko ({counts}).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
