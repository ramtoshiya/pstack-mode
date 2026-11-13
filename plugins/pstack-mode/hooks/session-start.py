import json
import os
import sys
from pathlib import Path


COMMAND = "<command-name>/pstack-mode:mode</command-name>"


def command_was_run(transcript):
    """Compaction drops the command's text, so find the user's /pstack-mode:mode run."""
    try:
        lines = Path(transcript).read_text().splitlines()
    except (OSError, TypeError):
        return False
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if (isinstance(entry, dict) and entry.get("type") == "user"
                and not entry.get("isSidechain") and isinstance(entry.get("message"), dict)):
            content = entry["message"].get("content")
            if isinstance(content, str) and COMMAND in content:
                return True
    return False


def main():
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    if event.get("hook_event_name") != "SessionStart":
        return
    if os.environ.get("PSTACK_MODE") != "1" and not (
            event.get("source") == "compact" and command_was_run(event.get("transcript_path"))):
        return
    root = Path(__file__).resolve().parent.parent
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
