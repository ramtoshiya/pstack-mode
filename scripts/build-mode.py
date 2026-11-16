#!/usr/bin/env python3
"""Build the selected pstack-mode plugin without changing the upstream tree."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "plugins" / "pstack-mode"
MIRROR_SHA = "74bcc61bd216687b1d6d480c28f109adfc9824ec"
CURSOR_SHA = "bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7"
WORKFLOWS = (
    "no-comments", "how", "why", "architect", "arena", "interrogate",
    "in-your-own-words", "show-me-your-work", "unslop", "technical-writing",
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
CURSOR_COORDINATOR = "patches/cursor-original/skills/no-comments/SKILL.md"
CURSOR_PROMPT = "patches/cursor-original/agents/comment-sicko.md"
CURSOR_HASHES = {
    CURSOR_COORDINATOR: "9cc934e7541c4db609deeb5fd4e5882c1a4d3956975b5ae1ee693ed340527b9b",
    CURSOR_PROMPT: "0fb37221ab2a9159714d38f1528898e82b9758b5750f244bbe2e575bb593a1de",
}
MANIFEST = "source-selection.json"
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


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def source_file(path, sources):
    full = ROOT / path
    if full.is_symlink() or not full.is_file():
        raise ValueError(f"source is not a regular file: {path}")
    data = full.read_bytes()
    executable = bool(full.stat().st_mode & 0o111)
    sources[path] = {"sha256": digest(data), "executable": executable}
    return data, executable


def selected_sources(sources):
    files = {}
    for skill in SKILLS:
        directory = ROOT / "skills" / skill
        if directory.is_symlink() or not (directory / "SKILL.md").is_file():
            raise ValueError(f"missing skill directory or SKILL.md: {directory}")
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"symlinks are not supported: {path}")
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                files[relative] = source_file(relative, sources)
    return files


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


def transform_skill(path, data):
    """Adapt routing and bundled links without changing the original policies."""
    adapted = {
        "skills/architect/SKILL.md", "skills/arena/SKILL.md", "skills/no-comments/SKILL.md",
        "skills/interrogate/SKILL.md", "skills/show-me-your-work/SKILL.md",
        "skills/architect/references/runner-prompt.md",
        "skills/principle-explain-the-number/SKILL.md",
    }
    if path not in adapted:
        return data
    text = data.decode("utf-8")
    if path == "skills/architect/SKILL.md":
        text = replace_paragraph(text, "Take the runners from the `architect runners` line", ROUTING +
            " Select the design runners under that policy and pass the roles to arena.")
    elif path == "skills/arena/SKILL.md":
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
        text = replace_paragraph(text, "After all Phase B candidates complete,",
            "After all Phase B candidates complete, select one readonly judge from a different "
            "model family than the parent under the shared routing policy. Try eligible "
            "other-family routes under that policy and their permitted fallbacks. If none "
            "can run, skip the judge, pick the base alone in Phase D, and say so. If the "
            "parent's model is unknown, try eligible routes and say that the family check "
            "did not run. The judge sees the rubric and the candidates by path label, scores "
            "each criterion, and recommends a base with rationale. It runs in parallel with "
            "your reading in Phase D. Don't spawn it while candidates are still writing.")
    elif path == "skills/no-comments/SKILL.md":
        original = (
        '1. Spawn `Task` with `subagent_type: "comment-sicko"`. Pass the scope. '
        "Pick each subagent's reasoning level and fast or standard speed for the job, "
        "per the Subagents section of the **poteto-mode** skill. Do not restate its rules."
        )
        replacement = (
        "1. " + ROUTING + " "
        'In Claude Code, spawn `Agent` with `subagent_type: "pstack-mode:comment-sicko"`. '
        'In Cursor with the pstack plugin, spawn `Task` with `subagent_type: "comment-sicko"`. '
        "Pass the scope. Do not restate its rules. If Comment Sicko is not registered, "
        "spawn a general subagent instead: "
        '`Agent` in Claude Code (`subagent_type: general-purpose`), `task` in OpenCode '
        '(`subagent_type: general`), or `spawn_agent` in Codex. Its prompt is '
        '[`references/comment-sicko.md`](references/comment-sicko.md) verbatim, then '
        "the scope. If the harness has no subagent tool, run that prompt yourself in a "
        "fresh pass over the scope."
        )
        text = replace_once(text, original, replacement)
    elif path == "skills/interrogate/SKILL.md":
        text = replace_once(text, "Read the `interrogate reviewers` line in place of `arena runners`.",
                            ROUTING + " Select adversaries using that policy.")
    elif path == "skills/show-me-your-work/SKILL.md":
        text = replace_once(text, "Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **poteto-mode** skill.", ROUTING)
    elif path == "skills/architect/references/runner-prompt.md":
        text = replace_once(text, "each on a different model", "assigned through the shared worker-routing policy")
    elif path == "skills/principle-explain-the-number/SKILL.md":
        text = replace_once(text, "with the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill",
                            "with the [benchmark checklist](references/benchmark-checklist.md)")
    return text.encode("utf-8")


def expected_package():
    sources = {}
    selected = selected_sources(sources)
    license_file = source_file("LICENSE", sources)
    coordinator = source_file(CURSOR_COORDINATOR, sources)
    prompt = source_file(CURSOR_PROMPT, sources)
    benchmark = source_file("skills/benchmark-checklist/SKILL.md", sources)
    source_file("scripts/build-mode.py", sources)
    for path, expected in CURSOR_HASHES.items():
        if sources[path]["sha256"] != expected:
            raise ValueError(f"pinned Cursor source hash mismatch: {path}")

    selected["skills/no-comments/SKILL.md"] = coordinator
    selected["skills/no-comments/references/comment-sicko.md"] = prompt
    files = {path: (transform_skill(path, data), executable)
             for path, (data, executable) in selected.items()}
    files["agents/comment-sicko.md"] = prompt
    files["skills/principle-explain-the-number/references/benchmark-checklist.md"] = benchmark
    files["LICENSE"] = license_file
    metadata = {
        "name": "pstack-mode",
        "description": "A session mode with workflow skills and principles from pstack.",
        "author": {"name": "Lauren Tan"},
        "repository": "https://github.com/cursor/plugins",
        "license": "MIT",
    }
    files[".claude-plugin/plugin.json"] = (json_bytes(metadata), False)
    files[".codex-plugin/plugin.json"] = (json_bytes({**metadata, "skills": "./skills/"}), False)
    files["plugin.json"] = (json_bytes({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        **metadata,
    }), False)
    mode_sources = {}
    mode_root = ROOT / "mode"
    if mode_root.is_symlink() or not mode_root.is_dir():
        raise ValueError("mode source is not a regular directory")
    mode_text, _ = source_file("mode/mode.md", sources)
    files[MODE_SKILL] = (mode_skill(mode_text), False)
    for path in sorted(mode_root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not supported: {path}")
        if path.is_file():
            destination = path.relative_to(mode_root).as_posix()
            reserved = set(files) | {MANIFEST}
            if any(destination == name or destination.startswith(name + "/")
                   or name.startswith(destination + "/") for name in reserved):
                raise ValueError(f"mode source conflicts with generated output: {destination}")
            source = path.relative_to(ROOT).as_posix()
            files[destination] = source_file(source, sources)
            mode_sources[destination] = source
    manifest = {
        "upstream_mirror": {"repository": "https://github.com/backnotprop/pstack", "commit": MIRROR_SHA},
        "canonical_cursor": {"repository": "https://github.com/cursor/plugins", "commit": CURSOR_SHA},
        "selected_skills": [f"skills/{name}" for name in SKILLS],
        "policy_overrides": {
            "skills/no-comments/SKILL.md": CURSOR_COORDINATOR,
            "skills/no-comments/references/comment-sicko.md": CURSOR_PROMPT,
            "agents/comment-sicko.md": CURSOR_PROMPT,
        },
        "bundled_references": {
            "skills/principle-explain-the-number/references/benchmark-checklist.md": "skills/benchmark-checklist/SKILL.md",
        },
        "mode_sources": mode_sources,
        "sources": dict(sorted(sources.items())),
        "outputs": {
            path: {"sha256": digest(data), "executable": executable}
            for path, (data, executable) in sorted(files.items())
        },
    }
    files[MANIFEST] = (json_bytes(manifest), False)
    return files


def unexpected_skill_files(files):
    expected = set(files)
    extra = []
    for skill in SKILLS:
        directory = OUTPUT / "skills" / skill
        if directory.is_symlink():
            extra.append(f"skills/{skill} (symlink)")
        elif directory.exists():
            for path in sorted(directory.rglob("*")):
                if path.is_symlink() or path.is_file():
                    relative = path.relative_to(OUTPUT).as_posix()
                    if relative not in expected or path.is_symlink():
                        extra.append(relative)
    return extra


def check(files):
    problems = []
    for relative, (data, executable) in sorted(files.items()):
        path = OUTPUT / relative
        if path.is_symlink() or not path.is_file():
            problems.append(f"missing or invalid: {relative}")
        elif path.read_bytes() != data or bool(path.stat().st_mode & 0o111) != executable:
            problems.append(f"stale: {relative}")
    problems.extend(f"unexpected selected-skill file: {path}" for path in unexpected_skill_files(files))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"Selection is current: {len(SKILLS)} skills, {len(files)} generated files.")
    return 0


def build(files):
    extras = unexpected_skill_files(files)
    if extras:
        raise ValueError("unexpected files in selected skill directories: " + ", ".join(extras))
    for relative, (data, executable) in sorted(files.items()):
        path = OUTPUT / relative
        if path.is_symlink():
            raise ValueError(f"output is a symlink: {relative}")
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
