import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMAND = "<command-name>/pstack-mode:mode</command-name>"
COMMAND_NAME = b"pstack-mode:mode"
RELAYED_COMMAND = re.compile(r"\A\[bb message from thread:[^\]\s]+\]\s*\n\s*/pstack-mode:mode\s*\Z")
BRIEF = re.compile(r"\bRead `?(/[^\s`]+)/mode\.md")
TURN_CHECK = (
    "[pstack-mode turn check] Make this your first step, before any other tool call: "
    "check the principle index in {root}/mode.md against this turn and read the leaf of "
    "each principle whose trigger fits. Apply them. In the reply, name each principle "
    "that shaped a decision and the choice it changed."
)


def user_text(line):
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    if (isinstance(entry, dict) and entry.get("type") == "user"
            and not entry.get("isSidechain") and isinstance(entry.get("message"), dict)):
        content = entry["message"].get("content")
        if isinstance(content, str):
            return content
    return None


def is_pstack_root(path):
    try:
        manifest = json.loads((path / ".claude-plugin/plugin.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("name") == "pstack-mode"


def brief_root(first_message):
    match = BRIEF.search(first_message)
    return Path(match[1]) if match and is_pstack_root(Path(match[1])) else None


def is_relayed_command(text):
    return isinstance(text, str) and RELAYED_COMMAND.match(text) is not None


def activated_root(transcript):
    first_seen = False
    try:
        with open(transcript, "rb") as lines:
            for line in lines:
                if first_seen and COMMAND_NAME not in line:
                    continue
                text = user_text(line)
                if text is None:
                    continue
                if COMMAND in text or is_relayed_command(text):
                    return ROOT
                if not first_seen:
                    first_seen = True
                    root = brief_root(text)
                    if root is not None:
                        return root
    except (OSError, TypeError):
        return None
    return None


def mode_context(root):
    return (root / "mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(root))


def emit(event_name, context):
    if len(context) > 10000:
        raise ValueError("hook context exceeds the host's 10000-character limit")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": event_name, "additionalContext": context
    }}))


def on_session_start(event):
    if os.environ.get("PSTACK_MODE") == "1":
        root = ROOT
    elif event.get("source") == "compact":
        root = activated_root(event.get("transcript_path"))
        if root is None:
            return
    else:
        return
    emit("SessionStart", mode_context(root))


def on_user_prompt(event):
    if os.environ.get("PSTACK_MODE") == "1":
        root = ROOT
    else:
        root = activated_root(event.get("transcript_path"))
    if root is None:
        if is_relayed_command(event.get("prompt")):
            emit("UserPromptSubmit", mode_context(ROOT))
        return
    emit("UserPromptSubmit", TURN_CHECK.format(root=root))


def main():
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    handler = {"SessionStart": on_session_start, "UserPromptSubmit": on_user_prompt}.get(
        event.get("hook_event_name"))
    if handler:
        handler(event)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError) as error:
        print(f"pstack-mode activation failed: {error}", file=sys.stderr)
        sys.exit(1)
