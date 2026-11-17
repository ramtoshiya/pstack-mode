import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import unittest.mock
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_mode", REPO / "scripts/build-mode.py")
build_mode = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_mode)
WORKFLOWS = {
    "no-comments", "how", "why", "architect", "arena", "interrogate",
    "in-your-own-words", "show-me-your-work", "unslop", "technical-writing",
    "correct", "statechart", "tdd", "blast-radius", "typescript-best-practices",
    "create-verification-skill", "maintain-verification-skill",
    "create-formal-verification-skill", "maintain-formal-verification-skill",
}
PRINCIPLES = {path.name for path in (REPO / "upstream/skills").glob("principle-*")}
ADAPTED = set(build_mode.TRANSFORMS) | {
    "skills/no-comments/SKILL.md", "skills/no-comments/references/comment-sicko.md",
}


def git_blob(commit, path):
    return subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", f"{commit}:{path}"],
                          capture_output=True, check=True).stdout


class BuildModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pstack-mode-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for directory in ("upstream/skills", "scripts", "mode"):
            shutil.copytree(REPO / directory, self.repo / directory, symlinks=True)
        shutil.copy2(REPO / "upstream/LICENSE", self.repo / "upstream/LICENSE")
        self.upstream = self.repo / "upstream"
        self.output = self.repo / "plugins/pstack-mode"
        self.env = {**os.environ, "GIT_DIR": str(REPO / ".git")}
        self.run_builder()

    def run_builder(self, *args, success=True, env=None):
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts/build-mode.py"), *args],
            text=True, capture_output=True, check=False, env=env or self.env,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_selection_copies_unadapted_files_exactly(self):
        skill_dirs = {path.name for path in (self.output / "skills").iterdir()}
        skill_dirs.remove("mode")
        self.assertEqual(len(PRINCIPLES), 24)
        self.assertEqual(skill_dirs, WORKFLOWS | PRINCIPLES)
        for skill in skill_dirs:
            source = self.upstream / "skills" / skill
            for src in (path for path in source.rglob("*") if path.is_file()):
                key = src.relative_to(self.upstream).as_posix()
                dest = self.output / key
                self.assertTrue(dest.is_file(), key)
                if key not in ADAPTED:
                    self.assertEqual(src.read_bytes(), dest.read_bytes(), key)
                    self.assertEqual(os.access(src, os.X_OK), os.access(dest, os.X_OK), key)
        self.assertEqual((self.output / "LICENSE").read_bytes(), (self.upstream / "LICENSE").read_bytes())
        for path in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            metadata = json.loads((self.output / path).read_text())
            self.assertEqual(metadata["name"], "pstack-mode")
            self.assertNotIn("version", metadata)

    def test_no_comments_keeps_cursor_policy_instead_of_mirror_exception(self):
        commit = build_mode.CURSOR_ORIGINALS
        prompt = git_blob(commit, "agents/comment-sicko.md")
        for path in ("agents/comment-sicko.md", "skills/no-comments/references/comment-sicko.md"):
            self.assertEqual((self.output / path).read_bytes(), prompt)
        original = git_blob(commit, "skills/no-comments/SKILL.md").decode()
        generated = (self.output / "skills/no-comments/SKILL.md").read_text()
        self.assertEqual(generated.split("\n1. ", 1)[0], original.split("\n1. ", 1)[0])
        self.assertEqual(generated.split("\n2. ", 1)[1], original.split("\n2. ", 1)[1])
        self.assertIn('subagent_type: "pstack-mode:comment-sicko"', generated)
        self.assertIn("If a keep is refuted or still ambiguous, delete it.", generated)
        self.assertIn("Reject a second, report it open, and fail `/no-comments`.", generated)
        self.assertIn("`REVIEW`", (self.upstream / "skills/no-comments/references/comment-sicko.md").read_text())
        self.assertNotIn("`REVIEW`", generated + prompt.decode())

    def test_build_fails_without_cursor_originals(self):
        empty = self.repo / "empty.git"
        subprocess.run(["git", "init", "-q", "--bare", str(empty)], check=True)
        result = self.run_builder("--check", success=False, env={**self.env, "GIT_DIR": str(empty)})
        self.assertIn(f"cannot read agents/comment-sicko.md at {build_mode.CURSOR_ORIGINALS}", result.stderr)

    def test_package_routes_workers_through_shared_policy(self):
        for name in ("architect", "arena", "no-comments", "interrogate", "show-me-your-work",
                     "maintain-verification-skill"):
            with self.subTest(skill=name):
                text = (self.output / "skills" / name / "SKILL.md").read_text()
                self.assertIn("ramtoshiya:worker-routing", text)
                self.assertIn("HOSTS.md", text)
        arena = (self.output / "skills/arena/SKILL.md").read_text()
        for phrase in ("different model family", "skip the judge", "readonly judge", "own output location"):
            self.assertIn(phrase, arena)
        for path in self.output.rglob("*.md"):
            text = path.read_text()
            for cursor_only in ("pstack-models", "poteto-mode", "grok-", "claude-opus-5-5", "claude-fable"):
                self.assertNotIn(cursor_only, text, path.relative_to(self.output))

    def test_package_relative_links_resolve(self):
        missing = []
        for path in self.output.rglob("*.md"):
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if target == "url" or target.startswith(("#", "http:", "https:", "mailto:")):
                    continue
                relative = target.split("#", 1)[0]
                if relative and not (path.parent / relative).exists():
                    missing.append(f"{path.relative_to(self.output)}: {target}")
        self.assertEqual(missing, [])
        ref = self.output / "skills/principle-explain-the-number/references/benchmark-checklist.md"
        self.assertEqual(ref.read_bytes(), (self.upstream / "skills/benchmark-checklist/SKILL.md").read_bytes())
        self.assertFalse((self.output / "skills/benchmark-checklist").exists())

    def test_build_fails_when_a_selected_skill_or_substitution_anchor_disappears(self):
        with unittest.mock.patch.multiple(build_mode, ROOT=self.repo, UPSTREAM=self.upstream), \
                unittest.mock.patch.dict(os.environ, self.env):
            build_mode.expected_package()
            for skill in build_mode.SKILLS:
                with self.subTest(skill=skill):
                    source = self.upstream / "skills" / skill
                    source.rename(self.repo / "removed")
                    with self.assertRaisesRegex(ValueError, "not a regular directory"):
                        build_mode.expected_package()
                    (self.repo / "removed").rename(source)
            for path in set(build_mode.TRANSFORMS) - {"skills/no-comments/SKILL.md"}:
                with self.subTest(path=path):
                    source = self.upstream / path
                    original = source.read_bytes()
                    source.write_text("rewritten upstream text\n")
                    with self.assertRaisesRegex(ValueError, "expected one"):
                        build_mode.expected_package()
                    source.write_bytes(original)

    def test_mode_names_only_skill_paths_that_ship(self):
        paths = re.findall(r"`(skills/[^`<]+)`", (self.output / "mode.md").read_text())
        self.assertIn("skills/create-verification-skill/SKILL.md", paths)
        self.assertEqual([path for path in paths if not (self.output / path).is_file()], [])

    def test_check_reports_drift_and_build_repairs_it(self):
        def expect(problem):
            self.assertIn(problem, self.run_builder("--check", success=False).stderr)
            self.run_builder()
            self.run_builder("--check")

        source = self.upstream / "skills/why/SKILL.md"
        source.write_text(source.read_text() + "drift\n")
        expect("stale: skills/why/SKILL.md")
        output = self.output / "skills/how/SKILL.md"
        output.write_text("drift\n")
        expect("stale: skills/how/SKILL.md")
        (self.output / "skills/show-me-your-work/scripts/log.sh").chmod(0o644)
        expect("stale: skills/show-me-your-work/scripts/log.sh")
        (self.upstream / "skills/how/helper.md").write_text("new helper\n")
        expect("missing: skills/how/helper.md")
        (self.output / "agents/leftover.md").write_text("no source\n")
        expect("unexpected: agents/leftover.md")
        self.assertFalse((self.output / "agents/leftover.md").exists())

    def test_mode_sources_land_at_plugin_root(self):
        mode = self.repo / "mode"
        sample = mode / "test-runtime/nested/config.txt"
        sample.parent.mkdir(parents=True)
        sample.write_text("runtime source\n")
        self.assertIn("missing: test-runtime/nested/config.txt",
                      self.run_builder("--check", success=False).stderr)
        self.run_builder()
        for source in mode.rglob("*"):
            if source.is_file():
                relative = source.relative_to(mode).as_posix()
                self.assertEqual((self.output / relative).read_bytes(), source.read_bytes())
        link = mode / "test-runtime/link"
        link.symlink_to(sample)
        self.assertIn("symlinks are not supported", self.run_builder(success=False).stderr)
        link.unlink()
        for collision in ("plugin.json", "skills/how/SKILL.md", "skills/mode/SKILL.md"):
            with self.subTest(collision=collision):
                path = mode / collision
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("conflict")
                self.assertIn(f"two sources generate {collision}", self.run_builder(success=False).stderr)
                path.unlink()

    def test_mode_command_loads_controller_within_codex_budget(self):
        skill = (self.output / "skills/mode/SKILL.md").read_text()
        header, body = skill.split("---\n\n", 1)
        self.assertIn("name: mode\n", header)
        self.assertIn("disable-model-invocation: true\n", header)
        self.assertLessEqual(len(skill.encode("utf-8")), 8000)
        self.assertIn("read the entire `mode.md`", body)
        self.assertIn("{{PLUGIN_ROOT}}", body)
        self.assertEqual((self.output / "mode.md").read_bytes(), (self.repo / "mode/mode.md").read_bytes())
        codex = (self.output / "skills/mode/agents/openai.yaml").read_text()
        self.assertIn("allow_implicit_invocation: false", codex)

    def test_oversized_mode_skill_fails_before_replacing_package(self):
        builder = self.repo / "scripts/build-mode.py"
        text = builder.read_text().replace('MAX_MODE_SKILL_BYTES = 8000', 'MAX_MODE_SKILL_BYTES = 1')
        builder.write_text(text)
        result = self.run_builder(success=False)
        self.assertIn("mode skill exceeds", result.stderr)
        self.assertTrue((self.output / "mode.md").is_file())

    def test_mode_command_needs_its_root_sentence_and_no_other_placeholder(self):
        mode = self.repo / "mode/mode.md"
        original = mode.read_text()
        mode.write_text(original.replace("Plugin root is `{{PLUGIN_ROOT}}`.", "Plugin root is the folder holding this file."))
        self.assertIn("Plugin root is `{{PLUGIN_ROOT}}`.", self.run_builder(success=False).stderr)
        mode.write_text(original + "\nRead `{{PLUGIN_ROOT}}/HOSTS.md` before spawning.\n")
        self.assertIn("PLUGIN_ROOT", self.run_builder(success=False).stderr)

    def test_hermes_registers_every_skill_under_its_directory_name(self):
        spec = importlib.util.spec_from_file_location("pstack_hermes", self.output / "__init__.py")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        calls = []
        context = types.SimpleNamespace(register_skill=lambda *args: calls.append(args))

        def parse_frontmatter(text):
            header = text.split("---\n", 2)[1]
            return dict(line.split(": ", 1) for line in header.splitlines() if ": " in line), ""

        parser = types.SimpleNamespace(parse_frontmatter=parse_frontmatter)
        with unittest.mock.patch.dict(sys.modules, {"agent": types.ModuleType("agent"), "agent.skill_utils": parser}):
            adapter.register(context)
        self.assertEqual(sorted(call[0] for call in calls), sorted(WORKFLOWS | PRINCIPLES | {"mode"}))
        for name, path, description, frontmatter in calls:
            self.assertEqual(path, (self.output / "skills" / name / "SKILL.md").resolve())
            self.assertTrue(description.strip(), name)
        self.assertIn("name: \"pstack-mode\"\n", (self.output / "plugin.yaml").read_text())

    def test_frontmatter_keeps_host_keys_and_rejects_what_a_host_would_misread(self):
        skill = self.upstream / "skills/how/SKILL.md"
        original = skill.read_text()
        self.assertIn("\ndisable-model-invocation: true\n", original)
        self.run_builder("--check")
        cases = (
            ("disable-model-invocation:", "disable-model-invokation: true",
             "'disable-model-invokation' is not in SKILL_FRONTMATTER"),
            ("name:", "name: why", "name must be 'how'"),
            ("description:", "description: Use it: always", "put the description value in double quotes"),
            ("description:", 'description: "Pick <one>"', "without < or >"),
            ("disable-model-invocation:", "disable-model-invocation: yes", "must be true or false"),
        )
        for key, line, error in cases:
            with self.subTest(line=line):
                lines = [line if entry.startswith(key) else entry for entry in original.split("\n")]
                skill.write_text("\n".join(lines))
                self.assertIn(error, self.run_builder("--check", success=False).stderr)
        skill.write_text(original)

    def test_check_ignores_bytecode_a_host_writes_into_the_package(self):
        cache = self.output / "__pycache__/__init__.cpython-314.pyc"
        cache.parent.mkdir()
        cache.write_bytes(b"bytecode")
        self.run_builder("--check")


if __name__ == "__main__":
    unittest.main()
