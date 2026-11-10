import json
import os
import sys
from pathlib import Path


def main():
    event = json.load(sys.stdin)
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    if event.get("hook_event_name") != "SessionStart":
        return
    root = Path(__file__).resolve().parent.parent
    context = (root / "mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(root))
    bindings = {
        name: os.environ[name]
        for name in (
            "PSTACK_CLAUDE_INSTANCE", "PSTACK_CODEX_INSTANCE", "PSTACK_CLAUDEX_INSTANCE"
        )
        if os.environ.get(name)
    }
    if bindings:
        context += "\nExperimental T3 provider bindings: " + json.dumps(bindings) + "\n"
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
