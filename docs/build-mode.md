# Build pstack-mode

The generator uses Python's standard library and git. Install Python 3 using the [Python downloads page](https://www.python.org/downloads/) or an existing Python environment. From the repository root, run:

```sh
python3 scripts/build-mode.py
python3 scripts/build-mode.py --check
python3 -m unittest discover -s tests
```

The generator owns `plugins/pstack-mode/`. It deletes the folder and writes the selected skills from `upstream/skills/`, the Cursor no-comments originals, every file under `mode/` at the plugin root, and a short `/pstack-mode:mode` entry skill that loads `mode.md`. The generator rejects an entry skill over 8,000 bytes before writing the package. It also validates every skill's frontmatter: only the keys in `SKILL_FRONTMATTER`, each on one line, a `name` that matches the skill folder, and a description of at most 1,024 characters without `<` or `>`. `--check` lists missing, stale, and unexpected files without writing. Each substitution must match its anchor text exactly once, and every selected skill must exist under `upstream/skills/`, so an upstream rewrite or removal stops the build instead of passing through unadapted. The tests break every substitution anchor and remove every selected skill in turn to prove that.

The repository's hooks run the check and the tests before each commit and merge. They also reject an `upstream/` that matches no mirror commit, and top-level paths outside this layout. Enable them once per clone:

```sh
git config core.hooksPath .githooks
```

Use `--check` to validate the skills, not Codex's skill-creator `quick_validate.py`. That validator allows only `name`, `description`, `license`, `allowed-tools`, and `metadata`, so it rejects every skill here for `disable-model-invocation`. Claude Code reads that key to keep the skills from loading on their own. Codex and Hermes ignore it and load the skills.

## Sync with upstream

`upstream/` holds the backnotprop/pstack mirror byte for byte. The `upstream` remote points at that mirror.

1. Run `git fetch upstream` and `git merge --no-commit -Xsubtree=upstream upstream/main`.
2. When the merge brings a new `upstream: cursor/plugins/pstack @ <sha>` commit, set `CURSOR_ORIGINALS` in `scripts/build-mode.py` to that commit.
3. Run the generator. If a substitution fails, read the new upstream text and update or delete the substitution.
4. Commit the merge, the generator change, and the generated plugin together.

## Release

Installed copies come from the commit that the `pstack-mode` entry in the
`ramtoshiya/skills` marketplace pins. To try a rebuild before release, start
Claude Code with `claude --plugin-dir plugins/pstack-mode`. To release, push
`main` to `ramtoshiya/pstack-mode`, then set that entry's `sha` to the pushed
commit as the skills repository's `docs/upstream-skills.md` describes.
