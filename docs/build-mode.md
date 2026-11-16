# Build pstack-mode

The generator uses Python's standard library and git. Install Python 3 using the [Python downloads page](https://www.python.org/downloads/) or an existing Python environment. From the repository root, run:

```sh
python3 scripts/build-mode.py
python3 scripts/build-mode.py --check
python3 -m unittest discover -s tests
```

The generator owns `plugins/pstack-mode/`. It deletes the folder and writes the selected skills, the Cursor no-comments originals, every file under `mode/` at the plugin root, and the `/pstack-mode:mode` command generated from `mode/mode.md`. `--check` lists missing, stale, and unexpected files without writing. Each substitution must match its anchor text exactly once, so an upstream rewrite stops the build instead of passing through unadapted.

## Sync with upstream

1. Run `git fetch upstream` and `git merge upstream/main`.
2. When the merge brings a new `upstream: cursor/plugins/pstack @ <sha>` commit, set `CURSOR_ORIGINALS` in `scripts/build-mode.py` to that commit.
3. Run the generator. If a substitution fails, read the new upstream text and update or delete the substitution.
4. Run the check and the tests, then commit the sources and the generated plugin together.
