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
    def run_hook(self, hook, event, env):
        return subprocess.run(
            [sys.executable, str(hook)], input=json.dumps(event),
            text=True, capture_output=True, env=env, check=False,
        )

    def test_opted_in_hook_delivers_mode_on_each_session_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="pstack hook ") as directory:
            root = Path(directory).resolve() / "plugin with spaces"
            shutil.copytree(REPO / "mode", root)
            env = {**os.environ, "PSTACK_MODE": "1"}
            expected = (root / "mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(root))
            for source in ("startup", "resume", "clear", "compact", "fork"):
                with self.subTest(source=source):
                    result = self.run_hook(root / "hooks/session-start.py",
                                           {"hook_event_name": "SessionStart", "source": source}, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    self.assertEqual(output["additionalContext"], expected)
                    self.assertLessEqual(len(expected), 10000)

    def test_hook_stays_silent_without_opt_in(self):
        env = {key: value for key, value in os.environ.items() if key != "PSTACK_MODE"}
        for value in (None, "0", "true"):
            with self.subTest(value=value):
                if value is not None:
                    env["PSTACK_MODE"] = value
                result = self.run_hook(REPO / "mode/hooks/session-start.py",
                                       {"hook_event_name": "SessionStart", "source": "startup"}, env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_compaction_restores_mode_only_after_the_user_ran_the_command(self):
        command = "<command-message>pstack-mode:mode</command-message>\n<command-name>/pstack-mode:mode</command-name>"
        user = {"type": "user", "isSidechain": False, "message": {"role": "user", "content": command}}
        cases = {
            "main session ran the command": ([user], "compact", True),
            "startup does not scan the transcript": ([user], "startup", False),
            "subagent ran it": ([{**user, "isSidechain": True}], "compact", False),
            "assistant quoted it": ([{**user, "type": "assistant"}], "compact", False),
            "never ran": ([{**user, "message": {"role": "user", "content": "hello"}}], "compact", False),
        }
        env = {key: value for key, value in os.environ.items() if key != "PSTACK_MODE"}
        hook = REPO / "mode/hooks/session-start.py"
        with tempfile.TemporaryDirectory() as directory:
            for name, (entries, source, active) in cases.items():
                with self.subTest(name):
                    transcript = Path(directory) / "session.jsonl"
                    transcript.write_text("not json\n" + "".join(json.dumps(e) + "\n" for e in entries))
                    result = self.run_hook(hook, {"hook_event_name": "SessionStart", "source": source,
                                                  "transcript_path": str(transcript)}, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(bool(result.stdout), active)
            result = self.run_hook(hook, {"hook_event_name": "SessionStart", "source": "compact",
                                          "transcript_path": str(Path(directory) / "missing.jsonl")}, env)
            self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_hook_ignores_other_events_and_reports_invalid_input(self):
        hook = REPO / "mode/hooks/session-start.py"
        for event, code in (({"hook_event_name": "SubagentStart"}, 0), ([], 1)):
            with self.subTest(event=event):
                result = self.run_hook(hook, event, {**os.environ, "PSTACK_MODE": "1"})
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(result.stdout, "")
                if code:
                    self.assertIn("hook input must be a JSON object", result.stderr)


if __name__ == "__main__":
    unittest.main()
