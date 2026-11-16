# Build pstack-mode

The generator uses Python's standard library and git. Install Python 3 using the [Python downloads page](https://www.python.org/downloads/) or an existing Python environment. From the repository root, run:

```sh
python3 scripts/build-mode.py
python3 scripts/build-mode.py --check
python3 -m unittest discover -s tests
```

The generator owns `plugins/pstack-mode/`. It deletes the folder and writes the selected skills from `upstream/skills/`, the Cursor no-comments originals, every file under `mode/` at the plugin root, and the `/pstack-mode:mode` command generated from `mode/mode.md`. `--check` lists missing, stale, and unexpected files without writing. Each substitution must match its anchor text exactly once, so an upstream rewrite stops the build instead of passing through unadapted.

The repository's pre-commit hook runs the check and the tests. Enable it once per clone:

```sh
git config core.hooksPath .githooks
```

## Sync with upstream

`upstream/` holds the backnotprop/pstack mirror byte for byte. The `upstream` remote points at that mirror.

1. Run `git fetch upstream` and `git merge --no-commit -Xsubtree=upstream upstream/main`.
2. When the merge brings a new `upstream: cursor/plugins/pstack @ <sha>` commit, set `CURSOR_ORIGINALS` in `scripts/build-mode.py` to that commit.
3. Run the generator. If a substitution fails, read the new upstream text and update or delete the substitution.
4. Run the check and the tests, then commit the merge, the generator change, and the generated plugin together.
5. Confirm that `upstream/` still matches the mirror: `git rev-parse HEAD:upstream upstream/main^{tree}` prints the same hash twice.
