import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


class ActivationTests(unittest.TestCase):
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
                    result = self.run_hook(root / "hooks/activation.py",
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
                result = self.run_hook(REPO / "mode/hooks/activation.py",
                                       {"hook_event_name": "SessionStart", "source": "startup"}, env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_compaction_restores_mode_only_after_the_user_or_brief_activated_it(self):
        command = "<command-message>pstack-mode:mode</command-message>\n<command-name>/pstack-mode:mode</command-name>"
        env = {key: value for key, value in os.environ.items() if key != "PSTACK_MODE"}
        hook = REPO / "mode/hooks/activation.py"
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

    def test_each_prompt_after_activation_gets_the_turn_check(self):
        command = "<command-message>pstack-mode:mode</command-message>\n<command-name>/pstack-mode:mode</command-name>"
        relayed = "[bb message from thread:thr_abc123]\n\n/pstack-mode:mode"
        env = {key: value for key, value in os.environ.items() if key != "PSTACK_MODE"}
        hook = REPO / "mode/hooks/activation.py"
        own_mode = (REPO / "mode/mode.md").read_text().replace("{{PLUGIN_ROOT}}", str(REPO / "mode"))
        check = f"principle index in {REPO / 'mode'}/mode.md against this turn"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory).resolve()
            root = directory / "dev/pstack-mode"
            (root / ".claude-plugin").mkdir(parents=True)
            (root / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "pstack-mode"}))
            brief = f"Read {root}/mode.md and {root}/HOSTS.md before work."
            brief_check = f"principle index in {root}/mode.md against this turn"

            def user(content, **extra):
                return {"type": "user", "isSidechain": False,
                        "message": {"role": "user", "content": content}, **extra}

            cases = {
                "never activated": ([user("hello")], "next", None),
                "typed command ran": ([user("hello"), user(command)], "next", check),
                "relayed command ran": ([user("hello"), user(relayed + "\n")], "next", check),
                "relay header with other text": ([user("[bb message from thread:thr_abc123]\n\nhello")], "next", None),
                "relayed text quoted mid-message": ([user("see " + relayed)], "next", None),
                "subagent ran it": ([user(command, isSidechain=True)], "next", None),
                "brief started the session": ([user(brief), user("go on")], "next", brief_check),
                "later message named the root": ([user("hello"), user(brief)], "next", None),
                "session with no transcript": ([], "next", None),
            }
            for name, (entries, prompt, expected) in cases.items():
                with self.subTest(name):
                    transcript = directory / "session.jsonl"
                    transcript.write_text("not json\n" + "".join(json.dumps(e) + "\n" for e in entries))
                    result = self.run_hook(hook, {"hook_event_name": "UserPromptSubmit", "prompt": prompt,
                                                  "transcript_path": str(transcript)}, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if expected is None:
                        self.assertEqual(result.stdout, "")
                        continue
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "UserPromptSubmit")
                    self.assertTrue(output["additionalContext"].startswith("[pstack-mode turn check]"))
                    self.assertIn(expected, output["additionalContext"])
                    self.assertNotIn("Pstack session mode", output["additionalContext"])

            transcript = directory / "empty.jsonl"
            transcript.write_text(json.dumps(user("hello")) + "\n")
            for name, prompt, expected in (
                ("relayed command loads the mode", relayed, own_mode),
                ("relay header with trailing newline", relayed + "\n", own_mode),
                ("typed command text is left to the command", "/pstack-mode:mode", ""),
                ("plain prompt", "hello", ""),
                ("relay header with other text", "[bb message from thread:thr_abc123]\n\nhello", ""),
                ("relayed other command", "[bb message from thread:thr_abc123]\n\n/pstack-mode:modes", ""),
            ):
                with self.subTest(name):
                    result = self.run_hook(hook, {"hook_event_name": "UserPromptSubmit", "prompt": prompt,
                                                  "transcript_path": str(transcript)}, env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else ""
                    self.assertEqual(context, expected)

            with self.subTest("PSTACK_MODE checks every prompt"):
                result = self.run_hook(hook, {"hook_event_name": "UserPromptSubmit", "prompt": "hello",
                                              "transcript_path": str(transcript)}, {**env, "PSTACK_MODE": "1"})
                self.assertIn(check, json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_hook_ignores_other_events_and_reports_invalid_input(self):
        hook = REPO / "mode/hooks/activation.py"
        for event, code in (({"hook_event_name": "SubagentStart"}, 0), ([], 1)):
            with self.subTest(event=event):
                result = self.run_hook(hook, event, {**os.environ, "PSTACK_MODE": "1"})
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(result.stdout, "")
                if code:
                    self.assertIn("hook input must be a JSON object", result.stderr)


if __name__ == "__main__":
    unittest.main()
