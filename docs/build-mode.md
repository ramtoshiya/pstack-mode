# Build pstack-mode

The generator uses Python's standard library. Install Python 3 using the [Python downloads page](https://www.python.org/downloads/) or an existing Python environment. From the repository root, run:

```sh
python3 scripts/build-mode.py
python3 scripts/build-mode.py --check
python3 -m unittest discover -s tests
```

The generator writes the selected plugin files under `plugins/pstack-mode/`. It copies every file under `mode/` to the corresponding path at the plugin root. The selection manifest records the source and output hashes. `--check` compares the output and manifest with the current sources. The generator rejects symlinks, conflicting output paths, and unexpected files inside a selected skill directory. It leaves other plugin files alone.
