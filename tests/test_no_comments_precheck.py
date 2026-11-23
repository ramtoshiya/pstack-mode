import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRECHECK = REPO / "plugins/pstack-mode/scripts/no-comments-precheck.py"
ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
SKIP, RUN, SCOPE_ERROR = 0, 1, 2


class PrecheckTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="no-comments-precheck-")
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.git("init", "-q", "-b", "main")
        self.write({"src/app.ts": "export const add = (a: number, b: number) => a + b;\n",
                    "src/legacy.ts": "// unscoped comment\nexport const old = 1;\n"})
        self.commit("base")
        self.git("switch", "-q", "-c", "feature")

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       cwd=self.repo, env=ENV, check=True, capture_output=True)

    def write(self, files):
        for name, text in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def precheck(self, *args):
        result = subprocess.run([sys.executable, str(PRECHECK), *args], cwd=self.repo, env=ENV,
                                text=True, capture_output=True, check=False)
        return result.returncode, result.stdout

    def test_scope_without_comments_skips_the_reviewer_with_the_report(self):
        self.write({"src/app.ts": 'export const url = "https://example.com/*";\nexport const slashes = /\\/\\//g;\n',
                    "src/new.py": "MARK = '#'\nprint(MARK)\n"})
        self.commit("clean change")
        code, output = self.precheck()
        self.assertEqual(code, SKIP, output)
        self.assertIn("clean         src/app.ts  (javascript)", output)
        self.assertIn("clean         src/new.py  (python)", output)
        self.assertNotIn("legacy.ts", output)
        self.assertIn("Skip Comment Sicko.", output)

    def test_added_comment_runs_the_reviewer(self):
        self.write({"src/app.ts": "// adds numbers\nexport const add = (a: number, b: number) => a + b;\n"})
        code, output = self.precheck()
        self.assertEqual(code, RUN, output)
        self.assertIn("comment       src/app.ts:1", output)
        self.assertIn("Result: run Comment Sicko", output)

    def test_existing_comment_in_a_scoped_file_runs_the_reviewer(self):
        self.write({"src/legacy.ts": "// unscoped comment\nexport const old = 2;\n"})
        self.commit("touch a line away from the comment")
        code, output = self.precheck("--base", "main")
        self.assertEqual(code, RUN, output)
        self.assertIn("comment       src/legacy.ts:1", output)

    def test_suppressions_run_the_reviewer(self):
        cases = {
            "lint.ts": "/* eslint-disable no-console */\nconsole.log(1);\n",
            "types.ts": "// @ts-ignore\nconst x: number = 'a';\n",
            "style.py": "import os  # noqa: F401\n",
            "lib.rs": "#[allow(dead_code)]\nfn unused() {}\n",
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                self.write({name: text})
                code, output = self.precheck(name)
                self.assertEqual(code, RUN, output)
                self.assertIn(f"suppression   {name}:1", output)

    def test_unrecognized_file_types_run_the_reviewer(self):
        self.write({"notes.foo": "nothing that looks like code\n", "tool": "plain text\n"})
        code, output = self.precheck("notes.foo", "tool")
        self.assertEqual(code, RUN, output)
        self.assertIn("unclassified  notes.foo  (no known comment syntax for this file type)", output)
        self.assertIn("unclassified  tool  (no known comment syntax for this file type)", output)

    def test_lexer_finds_comments_and_ignores_markers_inside_strings(self):
        cases = {
            "a.py": ('"""Docstring."""\nx = 1\n', RUN),
            "b.py": ('#!/usr/bin/env python3\nprint("#")\n"".join([])\n', SKIP),
            "c.sh": ('#!/bin/sh\necho "#" ${#x} $#\n', SKIP),
            "d.sh": ("ls  # list\n", RUN),
            "e.yaml": ('color: "#fff"\nname: don\'t\n', SKIP),
            "f.yaml": ("a: 1 # why\n", RUN),
            "g.css": ('a { background: url("//cdn/x.png"); }\n', SKIP),
            "h.css": ("/* banner */\na { color: red; }\n", RUN),
            "i.md": ("# Title\n\n```ts\nconst a = 'b';\n```\n", SKIP),
            "j.md": ("# Title\n\n```ts\n// narrated\nconst a = 1;\n```\n", RUN),
            "k.md": ("<!-- hidden -->\ntext\n", RUN),
            "l.html": ("<p>x</p>\n<script>\n// boot\nrun();\n</script>\n", RUN),
            "m.go": ("package m\n\nvar r = `//raw`\nvar c = '/'\n", SKIP),
            "n.json": ('{"url": "https://x/*"}\n', SKIP),
            "o.tsx": ("export const A = () => <div>\n  <b>hi</b>\n</div>;\n", SKIP),
        }
        for name, (text, expected) in cases.items():
            with self.subTest(name=name):
                self.write({name: text})
                code, output = self.precheck(name)
                self.assertEqual(code, expected, output)

    def test_text_the_lexer_cannot_settle_runs_the_reviewer(self):
        cases = {
            "unterminated.ts": "const a = 'oops;\n",
            "heredoc.sh": "cat <<EOF\ndon't\nEOF\n# real comment\necho can't\n",
            "fence.md": "```\nx = 1 # maybe\n```\n",
            "broken.py": "def f(:\n    pass\n",
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                self.write({name: text})
                code, output = self.precheck(name)
                self.assertEqual(code, RUN, output)
                self.assertIn(f"unclassified  {name}", output)

    def test_staged_scope_reads_the_index_and_unstaged_scope_includes_untracked_files(self):
        self.write({"src/app.ts": "// staged comment\nexport const a = 1;\n"})
        self.git("add", "src/app.ts")
        self.write({"src/app.ts": "export const a = 1;\n", "src/untracked.ts": "// draft\n"})
        code, output = self.precheck("--staged")
        self.assertEqual(code, RUN, output)
        self.assertIn("comment       src/app.ts:1", output)
        code, output = self.precheck("--unstaged", "src/untracked.ts")
        self.assertEqual(code, RUN, output)
        self.assertIn("comment       src/untracked.ts:1", output)
        self.assertNotIn("src/app.ts", output)

    def test_unresolvable_scope_runs_the_reviewer(self):
        for args in (("--base", "no-such-branch"), ("missing.ts",)):
            with self.subTest(args=args):
                code, output = self.precheck(*args)
                self.assertEqual(code, SCOPE_ERROR, output)
                self.assertIn("Result: run Comment Sicko.", output)


if __name__ == "__main__":
    unittest.main()
