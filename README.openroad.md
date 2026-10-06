# OpenROAD with Bazel and Python

This setup builds OpenROAD's command-line executable and its separate Python
wheel with Bazel, without root access. The installation lives in `.tools/`,
which is ignored by Git. Builds run on an Oscar compute node through Slurm.

## Status

**Installed and Python-verified.** The CLI, Python package, and compatibility
launcher are active at `.tools/openroad`. Source `.tools/openroad/env.sh` to use
them. Verification passed for `Tech`/`Design`, thread control, OpenDB creation,
database file write/read, and legacy `import odb, openroad, utl`.

Slurm job **6967004** compiled both Bazel targets successfully. Its initial
verification failed because the upstream wheel installs `python/openroad/`
outside the default package search path. A `.pth` file now exposes that package
root in the dedicated environment. The build script includes this repair.
The smoke test was also corrected for this revision's API: create `Tech` before
setting thread count and supply `dbTech` when creating a `dbChip`.

The original job's `build-status.txt` remains `exit_code=1` as a historical
record. The successful repair and verification are recorded in
`.tools/openroad/verification-status.txt` (`exit_code=0`), `python-smoke.log`,
`python-runner-smoke.log`, and `legacy-imports.log`. The CLI reports
`bazel-nostamp`; the exact source revision is in `build-versions.txt`.

## Pinned versions and prerequisites

- OpenROAD commit: `50927c93d1947a4cd9fa62ceaa887a3a81725709`.
- Bazel: `9.1.1`, matching that commit's `.bazelversion`; its binary download is
  checked against the upstream SHA-256 checksum.
- Oscar Python module: `python/3.11.11-5e66`.
- Linux x86-64, Git, curl, tar, a Slurm allocation, and outbound HTTPS access
  from the compute node for source, toolchain, and dependency downloads.

The build uses upstream's hermetic compiler dependencies and read-only remote
build cache. Source checkout, Bazel caches, and compilation use node-local
`$TMPDIR` or `/tmp`. Installation artifacts are copied to the repository.
The batch script requests one CPU, 32 GB RAM, and 24 hours; a cold build may
need substantial time. Bazel and numerical libraries are restricted to one CPU.

## Build and install

Inspect [build_openroad.sbatch](build_openroad.sbatch), then submit from the
repository root:

```bash
cd /oscar/data/sreda/mabdelat/ChipXplore
bash -n build_openroad.sbatch
sbatch build_openroad.sbatch
```

The job builds these targets:

```bash
bazel build --jobs=1 --//:platform=cli \
  //:tarfile //python/openroad:openroad_wheel
```

The full script adds local cache locations and resource limits. It installs the
packaged CLI with its runtime files, creates a dedicated Python virtual
environment, and installs the built wheel there. It publishes the installation
only after verification. The previous container-backed command at
`/users/mabdelat/local/bin/openroad` remains available through its absolute path.

This setup is for CLI and Python use; it does not build the Qt GUI.

## Activate and use Python

After the build succeeds:

```bash
cd /oscar/data/sreda/mabdelat/ChipXplore
source .tools/openroad/env.sh
openroad -version
python -c 'import openroad; from openroad import odb; print(openroad.__file__)'
```

**Bazel's CLI at this revision does not embed Python.** Its build sets
`BUILD_PYTHON=false`. Python support comes from the separate
`//python/openroad:openroad_wheel` target, which requires Python 3.10 or newer.
A `-Python` CLI feature flag is therefore expected; it does not describe the
installed Python wheel. Do not use `openroad -python` with this CLI.

New Python scripts can use the package directly:

```python
import openroad
from openroad import odb

tech = openroad.Tech()
openroad.set_thread_count(1)
design = openroad.Design(tech)
```

For ChipXplore scripts that use top-level `import odb` or `import utl`, the
installation provides `openroad-python`. This launcher aliases those names to
`openroad.odb` and `openroad.utl`, then executes the supplied script while
preserving its arguments. It uses the installation's Python environment.

Install application dependencies into that same environment when needed:

```bash
source .tools/openroad/env.sh
python -m pip install -r requirements.txt
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
openroad-python core/parsers/design/design_parser.py \
  --input ./designs/my-design \
  --pdk /path/to/sky130A/libs.ref \
  --stage routing \
  --format load \
  --output_dir ./output/routing
```

Run design parsing in a compute allocation. The build job does not install
ChipXplore's full requirements or validate an end-to-end design export: that
requires the original DEF/SDC snapshots and matching PDK files.

## Verify Python support

The build automatically runs [openroad_python_smoke.py](openroad_python_smoke.py)
through both the installed interpreter and compatibility launcher. The test:

1. Imports `openroad` and `openroad.odb`.
2. Constructs `Tech`, then sets and checks the OpenROAD thread count.
3. Constructs a `Design` object.
4. Creates an OpenDB database, block, and net.
5. Writes an ODB file, reads it into a second database, and checks the contents.

A separate check verifies legacy `import odb, openroad, utl` through the launcher.
These are runtime checks, not just compilation or import checks.

To repeat in a compute allocation:

```bash
source .tools/openroad/env.sh
python openroad_python_smoke.py
openroad-python openroad_python_smoke.py
cat .tools/openroad/python-smoke.log
cat .tools/openroad/python-runner-smoke.log
cat .tools/openroad/legacy-imports.log
cat .tools/openroad/verification-status.txt
```

The main smoke test must print:

```text
PASS: OpenROAD Tech/Design, thread control, OpenDB creation and file round trip
```

## Upstream references

- [Build instructions](https://github.com/The-OpenROAD-Project/OpenROAD/blob/50927c93d1947a4cd9fa62ceaa887a3a81725709/docs/user/Build.md)
- [Bazel configuration](https://github.com/The-OpenROAD-Project/OpenROAD/blob/50927c93d1947a4cd9fa62ceaa887a3a81725709/BUILD.bazel)
- [Python wheel target](https://github.com/The-OpenROAD-Project/OpenROAD/blob/50927c93d1947a4cd9fa62ceaa887a3a81725709/python/openroad/BUILD)
