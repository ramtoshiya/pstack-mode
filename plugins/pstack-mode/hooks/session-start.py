import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMAND = "<command-name>/pstack-mode:mode</command-name>"
BRIEF = re.compile(r"\bRead `?(/[^\s`]+)/mode\.md")


def user_texts(transcript):
    try:
        lines = Path(transcript).read_text().splitlines()
    except (OSError, TypeError):
        return
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if (isinstance(entry, dict) and entry.get("type") == "user"
                and not entry.get("isSidechain") and isinstance(entry.get("message"), dict)):
            content = entry["message"].get("content")
            if isinstance(content, str):
                yield content


def is_pstack_root(path):
    try:
        manifest = json.loads((path / ".claude-plugin/plugin.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("name") == "pstack-mode"


def brief_root(first_message):
    match = BRIEF.search(first_message)
    return Path(match[1]) if match and is_pstack_root(Path(match[1])) else None


def activated_root(transcript):
    texts = list(user_texts(transcript))
    if any(COMMAND in text for text in texts):
        return ROOT
    return brief_root(texts[0]) if texts else None


def main():
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    if event.get("hook_event_name") != "SessionStart":
        return
    if os.environ.get("PSTACK_MODE") == "1":
        root = ROOT
    elif event.get("source") == "compact":
        root = activated_root(event.get("transcript_path"))
        if root is None:
            return
    else:
        return
    context = (root / "mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(root))
    if len(context) > 10000:
        raise ValueError("mode context exceeds the host's 10000-character limit")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context
    }}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError) as error:
        print(f"pstack-mode activation failed: {error}", file=sys.stderr)
        sys.exit(1)
