import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = {
    "no-comments", "how", "why", "architect", "arena", "interrogate",
    "in-your-own-words", "show-me-your-work", "unslop", "technical-writing",
}


class BuildModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pstack-mode-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for directory in ("skills", "patches", "scripts"):
            shutil.copytree(REPO / directory, self.repo / directory)
        if (REPO / "mode").exists():
            shutil.copytree(REPO / "mode", self.repo / "mode", symlinks=True)
        shutil.copy2(REPO / "LICENSE", self.repo / "LICENSE")
        self.output = self.repo / "plugins/pstack-mode"
        self.run_builder()

    def run_builder(self, *args, success=True):
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts/build-mode.py"), *args],
            text=True, capture_output=True, check=False,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_selection_copies_complete_trees_and_records_sources(self):
        skill_dirs = {path.name for path in (self.output / "skills").iterdir()}
        self.assertIn("mode", skill_dirs)
        skill_dirs.remove("mode")
        principles = {path.name for path in (self.repo / "skills").glob("principle-*")}
        self.assertEqual(len(principles), 24)
        self.assertEqual(skill_dirs, WORKFLOWS | principles)
        self.assertTrue({"poteto-mode", "setup-pstack", "swarm"}.isdisjoint(skill_dirs))
        manifest = json.loads((self.output / "source-selection.json").read_text())
        self.assertEqual(manifest["upstream_mirror"]["commit"], "08547969e1dffaa6457ea65141cc62c1d9a2eef1")
        self.assertEqual(manifest["canonical_cursor"]["commit"], "de8ee15dd1194627d21eb5fcd41cb1873208dabb")
        self.assertEqual(set(manifest["selected_skills"]), {f"skills/{name}" for name in skill_dirs})
        for skill in skill_dirs:
            source = self.repo / "skills" / skill
            output = self.output / "skills" / skill
            source_files = {path.relative_to(source) for path in source.rglob("*") if path.is_file()}
            output_files = {path.relative_to(output) for path in output.rglob("*") if path.is_file()}
            extra = ({Path("references/benchmark-checklist.md")}
                     if skill == "principle-explain-the-number" else set())
            self.assertEqual(source_files | extra, output_files)
            for relative in source_files:
                src = source / relative
                dest = output / relative
                key = src.relative_to(self.repo).as_posix()
                self.assertEqual(manifest["sources"][key]["sha256"], hashlib.sha256(src.read_bytes()).hexdigest())
                if key not in {
                    "skills/no-comments/SKILL.md",
                    "skills/no-comments/references/comment-sicko.md",
                    "skills/how/SKILL.md", "skills/why/SKILL.md",
                    "skills/architect/SKILL.md", "skills/arena/SKILL.md",
                    "skills/interrogate/SKILL.md", "skills/show-me-your-work/SKILL.md",
                    "skills/architect/references/runner-prompt.md",
                    "skills/principle-explain-the-number/SKILL.md",
                }:
                    self.assertEqual(src.read_bytes(), dest.read_bytes(), key)
                    self.assertEqual(bool(src.stat().st_mode & 0o111), bool(dest.stat().st_mode & 0o111), key)
        self.assertEqual((self.output / "LICENSE").read_bytes(), (self.repo / "LICENSE").read_bytes())
        for path in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            metadata = json.loads((self.output / path).read_text())
            self.assertEqual(metadata["name"], "pstack-mode")
            self.assertNotIn("version", metadata)
        self.run_builder("--check")

    def test_original_policy_is_preserved_in_coordinator_and_both_prompts(self):
        original = self.repo / "patches/cursor-original"
        coordinator = (original / "skills/no-comments/SKILL.md").read_bytes()
        prompt = (original / "agents/comment-sicko.md").read_bytes()
        self.assertEqual(hashlib.sha256(coordinator).hexdigest(), "078ecfe224eafbb017f6476870612838bf6dbe38c0b697e12f0c887d0313f17e")
        self.assertEqual(hashlib.sha256(prompt).hexdigest(), "3e239e40b7b4b9beb2cf7f3ccc57f2388eb8b69bd1ba8ae888ef87ef6e0e2116")
        for path in ("agents/comment-sicko.md", "skills/no-comments/references/comment-sicko.md"):
            self.assertEqual((self.output / path).read_bytes(), prompt)
        generated = (self.output / "skills/no-comments/SKILL.md").read_text()
        original_text = coordinator.decode()
        self.assertEqual(generated.split("\n1. ", 1)[0], original_text.split("\n1. ", 1)[0])
        self.assertEqual(generated.split("\n2. ", 1)[1], original_text.split("\n2. ", 1)[1])
        self.assertIn('subagent_type: "pstack-mode:comment-sicko"', generated)
        self.assertIn("references/comment-sicko.md", generated)
        self.assertIn("spawn_agent", generated)
        self.assertIn("If a keep is refuted or still ambiguous, delete it.", generated)
        self.assertIn("Reject a second, report it open, and fail `/no-comments`.", generated)
        self.assertNotIn("`REVIEW`", generated)
        prompt_text = prompt.decode()
        self.assertIn("When I am not sure a keep clause applies, the comment dies.", prompt_text)
        self.assertIn("Doubt after the hunt is meat.", prompt_text)
        self.assertIn("Mark the exact guilty symbol `MUST KILL`.", prompt_text)
        self.assertNotIn("`REVIEW`", prompt_text)
        self.assertNotIn("names a problem the code has today", prompt_text)

    def test_generated_routes_keep_workflow_constraints(self):
        texts = {name: (self.output / "skills" / name / "SKILL.md").read_text()
                 for name in ("how", "why", "architect", "arena", "no-comments",
                              "interrogate", "show-me-your-work")}
        for name, text in texts.items():
            with self.subTest(skill=name):
                self.assertIn("ramtoshiya:worker-routing", text)
                self.assertIn("HOSTS.md", text)
                self.assertNotIn("poteto-mode", text)
                self.assertNotIn("pstack-models", text)
                self.assertNotIn("grok-4.7", text)
                self.assertNotIn("claude-opus-5-5", text)
        self.assertIn("readonly", texts["how"].lower())
        self.assertIn("Spawn one explainer", texts["how"])
        self.assertIn("2 to 4 angles", texts["how"])
        self.assertIn("one investigator per category", texts["why"])
        self.assertIn("references/epistemics.md", texts["why"])
        self.assertIn("MCP", texts["why"])
        self.assertIn("at least two structurally distinct candidates", texts["architect"])
        self.assertIn("own output location", texts["arena"])
        self.assertIn("different model family", texts["arena"])
        self.assertIn("skip the judge", texts["arena"])
        self.assertIn("readonly judge", texts["arena"])

    def test_package_relative_links_and_bundled_benchmark(self):
        missing = []
        for path in (self.output / "skills").rglob("*.md"):
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if target == "url" or target.startswith(("#", "http:", "https:", "mailto:")):
                    continue
                relative = target.split("#", 1)[0]
                if relative and not (path.parent / relative).is_file():
                    missing.append(f"{path.relative_to(self.output)}: {target}")
        self.assertEqual(missing, [])
        ref = self.output / "skills/principle-explain-the-number/references/benchmark-checklist.md"
        self.assertEqual(ref.read_bytes(), (self.repo / "skills/benchmark-checklist/SKILL.md").read_bytes())
        self.assertFalse((self.output / "skills/benchmark-checklist").exists())

    def test_check_detects_source_and_output_drift(self):
        cases = (
            (self.repo / "skills/why/references/epistemics.md", "source change"),
            (self.output / "skills/how/references/explorer-prompt.md", "output change"),
            (self.output / "source-selection.json", "manifest change"),
        )
        for path, label in cases:
            with self.subTest(label=label):
                original = path.read_bytes()
                path.write_bytes(original + b"\ndrift\n")
                result = self.run_builder("--check", success=False)
                self.assertIn("stale:", result.stderr)
                path.write_bytes(original)
        new_source = self.repo / "skills/how/references/new-helper.md"
        new_source.write_text("new helper\n")
        self.assertIn("missing or invalid: skills/how/references/new-helper.md", self.run_builder("--check", success=False).stderr)
        new_source.unlink()
        helper = self.output / "skills/show-me-your-work/scripts/log.sh"
        helper.chmod(0o644)
        self.assertIn("stale: skills/show-me-your-work/scripts/log.sh", self.run_builder("--check", success=False).stderr)
        helper.chmod(0o755)
        overlay = self.repo / "patches/cursor-original/agents/comment-sicko.md"
        original = overlay.read_bytes()
        overlay.write_bytes(original + b"drift")
        self.assertIn("pinned Cursor source hash mismatch", self.run_builder("--check", success=False).stderr)
        overlay.write_bytes(original)
        extra = self.output / "skills/how/unexpected.txt"
        extra.write_text("not generated")
        self.assertIn("unexpected selected-skill file", self.run_builder("--check", success=False).stderr)
        self.assertIn("unexpected files", self.run_builder(success=False).stderr)
        self.assertEqual(extra.read_text(), "not generated")
        extra.unlink()
        self.run_builder("--check")

    def test_rebuild_is_deterministic_and_leaves_other_plugin_files_alone(self):
        foreign = self.output / "agents/mode.md"
        foreign.write_text("parent-owned\n")
        before = {path.relative_to(self.output): path.read_bytes()
                  for path in self.output.rglob("*") if path.is_file()}
        self.run_builder()
        after = {path.relative_to(self.output): path.read_bytes()
                 for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(foreign.read_text(), "parent-owned\n")
        self.run_builder("--check")

    def test_mode_sources_generate_runtime_and_reject_symlinks_and_collisions(self):
        mode = self.repo / "mode"
        sample = mode / "test-runtime/nested/config.txt"
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_text("runtime source\n")
        result = self.run_builder("--check", success=False)
        self.assertIn("missing or invalid: test-runtime/nested/config.txt", result.stderr)
        self.run_builder()
        output = self.output / "test-runtime/nested/config.txt"
        self.assertEqual(output.read_bytes(), sample.read_bytes())
        manifest = json.loads((self.output / "source-selection.json").read_text())
        self.assertEqual(manifest["mode_sources"]["test-runtime/nested/config.txt"],
                         "mode/test-runtime/nested/config.txt")
        self.assertEqual(manifest["sources"]["mode/test-runtime/nested/config.txt"]["sha256"],
                         hashlib.sha256(sample.read_bytes()).hexdigest())
        self.assertEqual(manifest["outputs"]["test-runtime/nested/config.txt"]["sha256"],
                         hashlib.sha256(output.read_bytes()).hexdigest())
        for source in mode.rglob("*"):
            if source.is_file():
                relative = source.relative_to(mode).as_posix()
                self.assertEqual((self.output / relative).read_bytes(), source.read_bytes())
                self.assertEqual(manifest["mode_sources"][relative], f"mode/{relative}")
        sample.write_text("changed\n")
        self.assertIn("stale: test-runtime/nested/config.txt", self.run_builder("--check", success=False).stderr)
        sample.write_text("runtime source\n")
        link = mode / "test-runtime/link"
        link.symlink_to(sample)
        self.assertIn("symlinks are not supported", self.run_builder(success=False).stderr)
        link.unlink()
        link.symlink_to(sample.parent, target_is_directory=True)
        self.assertIn("symlinks are not supported", self.run_builder("--check", success=False).stderr)
        link.unlink()
        collision = mode / "plugin.json"
        collision.write_text("{}")
        self.assertIn("mode source conflicts with generated output", self.run_builder(success=False).stderr)
        collision.unlink()
        selected = mode / "skills/how/SKILL.md"
        selected.parent.mkdir(parents=True)
        selected.write_text("conflict")
        self.assertIn("mode source conflicts with generated output", self.run_builder(success=False).stderr)
        selected.unlink()
        selected.parent.rmdir()
        selected.parent.write_text("file conflicts with a generated directory")
        self.assertIn("mode source conflicts with generated output", self.run_builder(success=False).stderr)
        selected.parent.unlink()
        self.run_builder("--check")
        relocated = self.repo / "mode-input"
        mode.rename(relocated)
        self.assertIn("mode source is not a regular directory", self.run_builder(success=False).stderr)
        relocated.rename(mode)


    def test_mode_command_carries_current_mode_with_host_expanded_root(self):
        skill = (self.output / "skills/mode/SKILL.md").read_text()
        header, body = skill.split("---\n\n", 1)
        self.assertIn("name: mode\n", header)
        self.assertIn("disable-model-invocation: true\n", header)
        mode = (self.repo / "mode/mode.md").read_text()
        self.assertEqual(body, mode.replace("{{PLUGIN_ROOT}}", "${CLAUDE_PLUGIN_ROOT}"))
        self.assertNotIn("{{PLUGIN_ROOT}}", body)
        (self.repo / "mode/mode.md").write_text(mode + "Changed.\n")
        self.assertIn("stale: skills/mode/SKILL.md", self.run_builder("--check", success=False).stderr)
        (self.repo / "mode/mode.md").write_text(mode)
        collision = self.repo / "mode/skills/mode/SKILL.md"
        collision.parent.mkdir(parents=True)
        collision.write_text("conflict")
        self.assertIn("mode source conflicts with generated output", self.run_builder(success=False).stderr)

if __name__ == "__main__":
    unittest.main()
