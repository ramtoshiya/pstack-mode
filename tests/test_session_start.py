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

    def test_compaction_restores_mode_only_after_the_user_or_brief_activated_it(self):
        command = "<command-message>pstack-mode:mode</command-message>\n<command-name>/pstack-mode:mode</command-name>"
        env = {key: value for key, value in os.environ.items() if key != "PSTACK_MODE"}
        hook = REPO / "mode/hooks/session-start.py"
        own_mode = (REPO / "mode/mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(REPO / "mode"))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory).resolve()
            roots = {}
            for name, manifest_name in (("dev/pstack-mode", "pstack-mode"), ("other", "other-mode")):
                root = directory / name
                (root / ".claude-plugin").mkdir(parents=True)
                (root / ".claude-plugin/plugin.json").write_text(json.dumps({"name": manifest_name}))
                (root / "mode.md").write_text(f"{name} mode at {{{{PLUGIN_ROOT}}}}")
                roots[name] = root
            brief = f"Read {roots['dev/pstack-mode']}/mode.md and {roots['dev/pstack-mode']}/HOSTS.md before work."
            brief_mode = f"dev/pstack-mode mode at {roots['dev/pstack-mode']}"

            def user(content, **extra):
                return {"type": "user", "isSidechain": False,
                        "message": {"role": "user", "content": content}, **extra}

            cases = {
                "main session ran the command": ([user(command)], "compact", own_mode),
                "startup does not scan the transcript": ([user(command)], "startup", ""),
                "subagent ran it": ([user(command, isSidechain=True)], "compact", ""),
                "assistant quoted it": ([user(command, type="assistant")], "compact", ""),
                "never ran": ([user("hello")], "compact", ""),
                "brief named a pstack root": ([user(brief + "\n\n## Goal")], "compact", brief_mode),
                "brief quoted the path": ([user(f"Read `{roots['dev/pstack-mode']}/mode.md`")], "compact", brief_mode),
                "startup ignores the brief": ([user(brief)], "startup", ""),
                "brief named another mode": ([user(f"Read {roots['other']}/mode.md")], "compact", ""),
                "brief named a missing root": ([user(f"Read {directory}/gone/mode.md")], "compact", ""),
                "later message named the root": ([user("hello"), user(brief)], "compact", ""),
            }
            for name, (entries, source, expected) in cases.items():
                with self.subTest(name):
                    transcript = directory / "session.jsonl"
                    transcript.write_text("not json\n" + "".join(json.dumps(e) + "\n" for e in entries))
                    result = self.run_hook(hook, {"hook_event_name": "SessionStart", "source": source,
                                                  "transcript_path": str(transcript)}, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else ""
                    self.assertEqual(context, expected)
            result = self.run_hook(hook, {"hook_event_name": "SessionStart", "source": "compact",
                                          "transcript_path": str(directory / "missing.jsonl")}, env)
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
