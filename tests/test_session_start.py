import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


class SessionStartTests(unittest.TestCase):
    def test_relocated_hook_delivers_mode_on_each_session_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="pstack hook ") as directory:
            root = Path(directory).resolve() / "plugin with spaces"
            shutil.copytree(REPO / "mode", root)
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("PSTACK_")}
            env["PSTACK_CODEX_INSTANCE"] = "isolated codex"
            expected = (root / "mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(root))
            for source in ("startup", "resume", "clear", "compact", "fork"):
                with self.subTest(source=source):
                    result = subprocess.run(
                        [sys.executable, str(root / "hooks/session-start.py")],
                        input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
                        text=True, capture_output=True, env=env, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    context = output["additionalContext"]
                    mode, binding = context.split("\nExperimental T3 provider bindings: ")
                    self.assertEqual(mode, expected)
                    self.assertEqual(json.loads(binding), {"PSTACK_CODEX_INSTANCE": "isolated codex"})
                    self.assertLessEqual(len(context), 10000)

    def test_hook_ignores_other_events_and_reports_invalid_input(self):
        hook = REPO / "mode/hooks/session-start.py"
        for event, code in (({"hook_event_name": "SubagentStart"}, 0), ([], 1)):
            with self.subTest(event=event):
                result = subprocess.run(
                    [sys.executable, str(hook)], input=json.dumps(event),
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(result.stdout, "")
                if code:
                    self.assertIn("hook input must be a JSON object", result.stderr)


if __name__ == "__main__":
    unittest.main()
