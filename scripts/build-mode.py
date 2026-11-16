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
OUTPUT = ROOT / "plugins" / "pstack-mode"
CURSOR_ORIGINALS = "75cd8e69b29b5bc306e1ecc8d735950de5fb8323"
WORKFLOWS = (
    "no-comments", "how", "why", "architect", "arena", "interrogate",
    "in-your-own-words", "show-me-your-work", "unslop", "technical-writing",
    "correct", "statechart",
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
    "and follow it for model, effort, provider, quota, and retries. It does not "
    "activate lead mode. Read `HOSTS.md` at the plugin root for native tool names "
    "and worker activation."
)


MODE_SKILL = "skills/mode/SKILL.md"
MODE_SKILL_HEADER = """---
name: mode
description: Start pstack session mode in this conversation, with its workflow triggers, principles, and worker rules.
disable-model-invocation: true
---

"""


def mode_skill(mode_text):
    """Expose mode.md as an explicit command. The host expands the plugin root."""
    text = mode_text.decode("utf-8").replace("{{PLUGIN_ROOT}}", "${CLAUDE_PLUGIN_ROOT}")
    return (MODE_SKILL_HEADER + text).encode("utf-8")


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def tree(directory):
    """Map each regular file under directory to its bytes and executable bit."""
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
    """Read Cursor's file from the mirror commit that copies cursor/plugins/pstack exactly."""
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


def architect(text):
    return replace_paragraph(text, "Take the runners from the `architect runners` line", ROUTING +
        " Select the design runners under that policy and pass the roles to arena.")


def arena(text):
    text = replace_line(text, "3. Pick the runners.",
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
        "Pick each subagent's reasoning level and fast or standard speed for the job, "
        "per the Subagents section of the **poteto-mode** skill. Do not restate its rules.",
        "1. " + ROUTING + " "
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
    "skills/architect/SKILL.md": architect,
    "skills/arena/SKILL.md": arena,
    "skills/no-comments/SKILL.md": no_comments,
    "skills/interrogate/SKILL.md": lambda text: replace_once(text,
        "Read the `interrogate reviewers` line in place of `arena runners`.",
        ROUTING + " Select adversaries using that policy."),
    "skills/show-me-your-work/SKILL.md": lambda text: replace_once(text,
        "Pick each subagent's reasoning level and fast or standard speed for the job, "
        "per the Subagents section of the **poteto-mode** skill.", ROUTING),
    "skills/architect/references/runner-prompt.md": lambda text: replace_once(text,
        "each on a different model", "assigned through the shared worker-routing policy"),
    "skills/principle-explain-the-number/SKILL.md": lambda text: replace_once(text,
        "with the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill",
        "with the [benchmark checklist](references/benchmark-checklist.md)"),
}


def expected_package():
    files = {}

    def add(path, data, executable=False):
        if path in files:
            raise ValueError(f"two sources generate {path}")
        files[path] = (data, executable)

    sources = {}
    for skill in SKILLS:
        for relative, entry in tree(ROOT / "skills" / skill).items():
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
        (ROOT / "skills/benchmark-checklist/SKILL.md").read_bytes())
    add("LICENSE", (ROOT / "LICENSE").read_bytes())
    metadata = {
        "name": "pstack-mode",
        "description": "A session mode with workflow skills and principles from pstack.",
        "author": {"name": "Lauren Tan"},
        "repository": "https://github.com/cursor/plugins",
        "license": "MIT",
    }
    add(".claude-plugin/plugin.json", json_bytes(metadata))
    add(".codex-plugin/plugin.json", json_bytes({**metadata, "skills": "./skills/"}))
    add("plugin.json", json_bytes({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", **metadata,
    }))
    mode = tree(ROOT / "mode")
    add(MODE_SKILL, mode_skill(mode["mode.md"][0]))
    for relative, (data, executable) in mode.items():
        add(relative, data, executable)
    return files


def on_disk():
    if not OUTPUT.exists():
        return {}
    return {path.relative_to(OUTPUT).as_posix(): path
            for path in OUTPUT.rglob("*") if path.is_file() or path.is_symlink()}


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
