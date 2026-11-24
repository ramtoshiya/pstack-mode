#!/usr/bin/env python3
"""Build the selected pstack-mode plugin without changing the upstream tree."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream"
OUTPUT = ROOT / "plugins" / "pstack-mode"
CURSOR_ORIGINALS = "8260de23663c7850b4397b1a1a9fce58f52dee3c"
WORKFLOWS = (
    "no-comments", "how", "why", "architect", "arena", "interrogate",
    "in-your-own-words", "show-me-your-work", "unslop", "technical-writing",
    "correct", "statechart", "tdd", "blast-radius", "typescript-best-practices",
    "create-verification-skill", "maintain-verification-skill",
    "create-formal-verification-skill", "maintain-formal-verification-skill",
)
PRINCIPLES = (
    "principle-attack-the-premise",
    "principle-boundary-discipline",
    "principle-build-the-lever",
    "principle-encode-lessons-in-structure",
    "principle-exhaust-the-design-space",
    "principle-experience-first",
    "principle-explain-the-number",
    "principle-fix-root-causes",
    "principle-foundational-thinking",
    "principle-guard-the-context-window",
    "principle-laziness-protocol",
    "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis",
    "principle-minimize-reader-load",
    "principle-model-the-domain",
    "principle-never-block-on-the-human",
    "principle-outcome-oriented-execution",
    "principle-prove-it-works",
    "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units",
    "principle-subtract-before-you-add",
    "principle-test-behavior-not-implementation",
    "principle-type-system-discipline",
)
SKILLS = tuple(sorted(WORKFLOWS + PRINCIPLES))
ROUTING = (
    "Before selecting workers, read the shared `ramtoshiya:worker-routing` skill "
    "and follow it for model, effort, provider, quota, and retries. Read `HOSTS.md` "
    "at the plugin root for native tool names "
    "and worker activation."
)


MODE_SKILL = "skills/mode/SKILL.md"
MODE_SKILL_HEADER = """---
name: mode
description: Start pstack session mode in this conversation, with its workflow triggers, principles, and worker rules.
disable-model-invocation: true
---

"""


MODE_ROOT = "Plugin root is `{{PLUGIN_ROOT}}`."
MODE_SKILL_BODY = """# Pstack session mode

Before starting the task, read the entire `mode.md` at the installed plugin root and follow it for this session. The root is the directory containing this skill's `skills/mode/` folder. Resolve it from this skill's path. In `mode.md`, interpret `{{PLUGIN_ROOT}}` as that root. If you cannot read the file, report the failure and stop.

After compaction, retain the plugin root and reload `mode.md` before continuing if the host has not restored it.
"""
MAX_MODE_SKILL_BYTES = 8000
SKILL_FRONTMATTER = ("name", "description", "disable-model-invocation")
YAML_INDICATORS = "'[{>|&*!%@`#"


def mode_skill(mode_text):
    text = replace_once(mode_text.decode("utf-8"), MODE_ROOT, "")
    if "{{PLUGIN_ROOT}}" in text:
        raise ValueError("mode.md may name {{PLUGIN_ROOT}} only in its plugin root sentence")
    skill = (MODE_SKILL_HEADER + MODE_SKILL_BODY).encode("utf-8")
    if len(skill) > MAX_MODE_SKILL_BYTES:
        raise ValueError(f"mode skill exceeds {MAX_MODE_SKILL_BYTES} bytes")
    return skill


def check_skill_frontmatter(path, data):
    lines = data.decode("utf-8").split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError(f"{path}: frontmatter must open and close with a --- line")
    fields = {}
    for line in lines[1:lines.index("---", 1)]:
        key = line.split(":", 1)[0]
        if key not in SKILL_FRONTMATTER:
            raise ValueError(f"{path}: frontmatter key {key!r} is not in SKILL_FRONTMATTER in "
                             "scripts/build-mode.py. Add it there once Claude Code, Codex, and Hermes accept it.")
        value = line[len(key) + 2:]
        if not line.startswith(key + ": ") or key in fields:
            raise ValueError(f"{path}: write {key} once, as `{key}: value` on one line")
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                raise ValueError(f"{path}: {key} must be one double-quoted string") from None
        elif not value or value[0] in YAML_INDICATORS or ": " in value or " #" in value:
            raise ValueError(f"{path}: put the {key} value in double quotes")
        fields[key] = value
    skill = path.split("/")[1]
    if fields.get("name") != skill:
        raise ValueError(f"{path}: name must be {skill!r}, the skill's directory name")
    description = fields.get("description", "")
    if not 0 < len(description) <= 1024 or "<" in description or ">" in description:
        raise ValueError(f"{path}: description must be 1 to 1024 characters without < or >")
    if fields.get("disable-model-invocation", "false") not in ("true", "false"):
        raise ValueError(f"{path}: disable-model-invocation must be true or false")


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def tree(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"not a regular directory: {directory.relative_to(ROOT)}")
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not supported: {path.relative_to(ROOT)}")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = (
                path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return files


def cursor_original(path):
    result = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "blob", f"{CURSOR_ORIGINALS}:{path}"],
        capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"cannot read {path} at {CURSOR_ORIGINALS}: "
                         + result.stderr.decode(errors="replace").strip())
    return result.stdout


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one occurrence of {old[:80]!r}")
    return text.replace(old, new, 1)


def replace_paragraph(text, start, replacement):
    if text.count(start) != 1:
        raise ValueError(f"expected one paragraph starting with {start!r}")
    offset = text.index(start)
    end = text.find("\n\n", offset)
    if end == -1:
        raise ValueError(f"unterminated paragraph starting with {start!r}")
    return text[:offset] + replacement + text[end:]


def replace_line(text, start, replacement):
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.startswith(start)]
    if len(matches) != 1:
        raise ValueError(f"expected one line starting with {start!r}")
    index = matches[0]
    lines[index] = replacement + ("\n" if lines[index].endswith("\n") else "")
    return "".join(lines)


def delete_line(text, start):
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.startswith(start)]
    if len(matches) != 1:
        raise ValueError(f"expected one line starting with {start!r}")
    del lines[matches[0]]
    return "".join(lines)


def attack_the_premise(text):
    text = replace_once(text,
        "Apply when two or more fixes that share one premise have failed the same gate.",
        "Apply when two or more fixes that share one premise have failed the same gate, "
        "a sweep of settings stops short of the target, or you explain the remaining "
        "failures as a limit of the tool.")
    text = replace_once(text,
        "suspect the premise, not the fixes.\n",
        "suspect the premise, not the fixes. A sweep of settings that stops short of the "
        "target counts, because each setting is a fix that failed. So does a remaining "
        "failure that you explain as a limit of the tool, because the limit usually holds "
        "only on the path the fixes share.\n")
    return replace_once(text,
        "Look at how the failures are distributed, not only at how large they are.\n",
        "Look at how the failures are distributed, not only at how large they are.\n"
        "- If you judged results against another source of the same value, such as a "
        "second screen, file, or API that you used as ground truth, test that source as "
        "the answer first. You already trust it more than the path you are fixing.\n")


def arena(text):
    text = replace_line(text, "3. Pick the runners",
        "3. Pick the runners. " + ROUTING + " Use two runners by default, or one "
        "when the caller specifies one. Add runners for multiple design directions. "
        "Use the same model N times when work is generation-bound rather than judgment-sensitive. "
        "If a runner is unavailable, follow the routing policy's retry and provider rules. "
        "Replace dropped runners with eligible runners until two remain, or one when "
        "one was selected. Reuse an eligible runner's model if needed and say so. "
        "If the host cannot start enough workers, report the shortfall.")
    text = replace_once(text, "Spawn all N subagents in one message with `run_in_background: true`,",
                        "Spawn all N subagents in parallel using the host's supported delegation tools,")
    return replace_paragraph(text, "After all Phase B candidates complete,",
        "After all Phase B candidates complete, select one readonly judge from a different "
        "model family than the parent under the shared routing policy. Try eligible "
        "other-family routes under that policy and their permitted fallbacks. If none "
        "can run, skip the judge, pick the base alone in Phase D, and say so. If the "
        "parent's model is unknown, try eligible routes and say that the family check "
        "did not run. The judge sees the rubric and the candidates by path label, scores "
        "each criterion, and recommends a base with rationale. It runs in parallel with "
        "your reading in Phase D. Don't spawn it while candidates are still writing.")


def no_comments(text):
    return replace_once(text,
        '1. Spawn `Task` with `subagent_type: "comment-sicko"`. Pass the scope. '
        "Pick each subagent's reasoning level for the job, "
        "per the Subagents section of the **poteto-mode** skill. Do not restate its rules.",
        "1. In the reviewed repository, run `python3` on "
        "[`scripts/no-comments-precheck.py`](../../scripts/no-comments-precheck.py) at the plugin root. Pass the caller's files as "
        "arguments, `--staged` or `--unstaged` for a staged or unstaged diff, or `--base <branch>` "
        "for a branch diff. A diff option also takes paths that limit it. With no arguments it "
        "scans the diff against `main`. It scans the whole content of every scoped file. If it "
        "exits 0, the scope has no comments, docstrings, or suppressions: do not spawn Comment "
        "Sicko, skip the remaining steps, and report its output as the result. On any other "
        "exit, continue. " + ROUTING + " "
        'In Claude Code, spawn `Agent` with `subagent_type: "pstack-mode:comment-sicko"`. '
        'In Cursor with the pstack plugin, spawn `Task` with `subagent_type: "comment-sicko"`. '
        "Pass the scope. Do not restate its rules. If Comment Sicko is not registered, "
        "spawn a general subagent instead: "
        '`Agent` in Claude Code (`subagent_type: general-purpose`), `task` in OpenCode '
        '(`subagent_type: general`), or `spawn_agent` in Codex. Its prompt is '
        '[`references/comment-sicko.md`](references/comment-sicko.md) verbatim, then '
        "the scope. If the harness has no subagent tool, run that prompt yourself in a "
        "fresh pass over the scope.")


TRANSFORMS = {
    "skills/arena/SKILL.md": arena,
    "skills/principle-attack-the-premise/SKILL.md": attack_the_premise,
    "skills/no-comments/SKILL.md": no_comments,
    "skills/interrogate/SKILL.md": lambda text: replace_once(text,
        "Read the `interrogate reviewers` line in place of `arena runners`.",
        ROUTING + " Select adversaries using that policy."),
    "skills/show-me-your-work/SKILL.md": lambda text: replace_once(text,
        "Pick each subagent's reasoning level for the job, "
        "per the Subagents section of the **poteto-mode** skill.", ROUTING),
    "skills/principle-explain-the-number/SKILL.md": lambda text: replace_once(text,
        "run the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill",
        "run the [benchmark checklist](references/benchmark-checklist.md)"),
    "skills/principle-type-system-discipline/SKILL.md": lambda text: replace_once(text,
        "see the **typescript-best-practices** skill.",
        "see the [typescript-best-practices](../typescript-best-practices/SKILL.md) skill."),
    "skills/correct/SKILL.md": lambda text: replace_once(text,
        "Last, keep a table in the agent instruction file that pairs each rule with what enforces it. "
        "When the operator corrects you, fix the mistake and add the rule. "
        "If the rule was already there and nothing enforces it, that's a repeat, "
        "so fix it at the highest level in the same change. Drop a rule once its mistake can't happen.",
        "Last, keep a table in the agent instruction file of the rules that only judgment enforces. "
        "A rule that architecture, a type, a lint, or a test enforces gets no row, "
        "because its error already tells the agent the fix. "
        "When the operator corrects you, fix the mistake at the highest level that works, "
        "and add a row only when that level is docs. "
        "If a row's mistake happens again, that's a repeat, so fix it at a higher level in the same change "
        "and drop the row. Drop a row once its mistake can't happen."),
    "skills/typescript-best-practices/SKILL.md": lambda text: delete_line(text, "paths: "),
    "skills/maintain-verification-skill/SKILL.md": lambda text: replace_once(text,
        "One read-only subagent per feature file, launched concurrently.",
        "One read-only subagent per feature file, launched concurrently. " + ROUTING),
}


def expected_package():
    files = {}

    def add(path, data, executable=False):
        if path in files:
            raise ValueError(f"two sources generate {path}")
        files[path] = (data, executable)

    sources = {}
    for skill in SKILLS:
        for relative, entry in tree(UPSTREAM / "skills" / skill).items():
            if relative == "agents/openai.yaml":
                continue
            sources[f"skills/{skill}/{relative}"] = entry
    prompt = cursor_original("agents/comment-sicko.md")
    sources["skills/no-comments/SKILL.md"] = (cursor_original("skills/no-comments/SKILL.md"), False)
    sources["skills/no-comments/references/comment-sicko.md"] = (prompt, False)
    for path, (data, executable) in sources.items():
        if path in TRANSFORMS:
            data = TRANSFORMS[path](data.decode("utf-8")).encode("utf-8")
        add(path, data, executable)
    add("agents/comment-sicko.md", prompt)
    add("skills/principle-explain-the-number/references/benchmark-checklist.md",
        (UPSTREAM / "skills/benchmark-checklist/SKILL.md").read_bytes())
    add("LICENSE", (UPSTREAM / "LICENSE").read_bytes())
    metadata = {
        "name": "pstack-mode",
        "description": "A session mode with workflow skills and principles from pstack.",
        "author": {"name": "Lauren Tan"},
        "repository": "https://github.com/cursor/plugins",
        "license": "MIT",
    }
    add(".claude-plugin/plugin.json", json_bytes(metadata))
    add(".codex-plugin/plugin.json", json_bytes({**metadata, "skills": "./skills/"}))
    add("plugin.yaml", "".join(f"{key}: {json.dumps(metadata[key])}\n" for key in ("name", "description")).encode())
    mode = tree(ROOT / "mode")
    add(MODE_SKILL, mode_skill(mode["mode.md"][0]))
    for relative, (data, executable) in mode.items():
        add(relative, data, executable)
    for path, (data, _) in files.items():
        if path.startswith("skills/") and path.endswith("/SKILL.md") and path.count("/") == 2:
            check_skill_frontmatter(path, data)
    return files


def on_disk():
    if not OUTPUT.exists():
        return {}
    return {path.relative_to(OUTPUT).as_posix(): path
            for path in OUTPUT.rglob("*")
            if (path.is_file() or path.is_symlink()) and "__pycache__" not in path.relative_to(OUTPUT).parts}


def check(files):
    existing = on_disk()
    problems = []
    for relative in sorted(set(files) | set(existing)):
        path = existing.get(relative)
        if path is None:
            problems.append(f"missing: {relative}")
        elif relative not in files:
            problems.append(f"unexpected: {relative}")
        elif path.is_symlink() or (path.read_bytes(), bool(path.stat().st_mode & 0o111)) != files[relative]:
            problems.append(f"stale: {relative}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        print("plugins/pstack-mode is out of date. Run python3 scripts/build-mode.py.", file=sys.stderr)
        return 1
    print(f"Selection is current: {len(SKILLS)} skills, {len(files)} generated files.")
    return 0


def build(files):
    if OUTPUT.is_symlink():
        raise ValueError("output is a symlink")
    shutil.rmtree(OUTPUT, ignore_errors=True)
    for relative, (data, executable) in sorted(files.items()):
        path = OUTPUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        os.chmod(path, 0o755 if executable else 0o644)
    print(f"Built {len(SKILLS)} skills, {len(files)} generated files in {OUTPUT}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated files without writing")
    args = parser.parse_args()
    try:
        files = expected_package()
        if args.check:
            return check(files)
        build(files)
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"build-mode: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
