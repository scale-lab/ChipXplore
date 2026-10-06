#!/bin/bash -l
#SBATCH --job-name=chipxplore-openroad
#SBATCH --partition=batch
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=openroad-build-%j.log
set -euo pipefail
exec 9>"/tmp/${USER}.agent-lock"
flock -n 9 || exit 1
: "${SLURM_JOB_ID:?Submit this script through sbatch}"
ROOT="${SLURM_SUBMIT_DIR:?}"
REV=50927c93d1947a4cd9fa62ceaa887a3a81725709
BAZEL_VERSION=9.1.1
WORK=$(mktemp -d "${TMPDIR:-/tmp}/chipxplore-openroad.XXXXXX")
PREFIX="$ROOT/.tools/openroad-builds/$REV-$SLURM_JOB_ID"
mkdir -p "$PREFIX/bin" "$PREFIX/wheels"
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$PREFIX/build-status.txt"; exit "$rc"' EXIT
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export BAZELISK_HOME="$WORK/bazelisk"
module load python/3.11.11-5e66
python3 -m venv "$PREFIX/venv"
cd "$WORK"
curl --fail --location --retry 3 -o bazel "https://releases.bazel.build/$BAZEL_VERSION/release/bazel-$BAZEL_VERSION-linux-x86_64"
curl --fail --location --retry 3 -o bazel.sha256 "https://releases.bazel.build/$BAZEL_VERSION/release/bazel-$BAZEL_VERSION-linux-x86_64.sha256"
printf '%s  bazel\n' "$(awk '{print $1}' bazel.sha256)" | sha256sum -c -
chmod +x bazel
git init OpenROAD
cd OpenROAD
git remote add origin https://github.com/The-OpenROAD-Project/OpenROAD.git
git fetch --depth 1 origin "$REV"
git checkout --detach FETCH_HEAD
git -c submodule.fetchJobs=1 submodule update --init --recursive --depth 1
"$WORK/bazel" --batch --output_user_root="$WORK/bazel-output" build \
  --jobs=1 --local_resources=cpu=1 --local_resources=memory=24000 \
  --loading_phase_threads=1 --repository_cache="$WORK/repository-cache" \
  --disk_cache="$WORK/disk-cache" --//:platform=cli \
  //:tarfile //python/openroad:openroad_wheel
# Preserve the packaged runtime layout; do not copy only the executable.
tar -xf bazel-bin/packaging/openroad.tar -C "$PREFIX/bin"
cp bazel-bin/python/openroad/*.whl "$PREFIX/wheels/"
"$PREFIX/venv/bin/python" -m pip install --no-deps "$PREFIX"/wheels/*.whl
# Upstream wheel preserves python/openroad; expose that package root explicitly.
"$PREFIX/venv/bin/python" - <<'PYPATH'
import site
from pathlib import Path
for directory in site.getsitepackages():
    base = Path(directory)
    if (base / "python/openroad/__init__.py").is_file():
        (base / "openroad-package-root.pth").write_text("python\n")
        break
else:
    raise RuntimeError("OpenROAD wheel package directory is missing")
PYPATH
# Compatibility entry point for ChipXplore's legacy top-level odb/utl imports.
cat > "$PREFIX/bin/openroad-python" <<EOF
#!/bin/bash
exec "$PREFIX/venv/bin/python" "$PREFIX/python_runner.py" "\$@"
EOF
cat > "$PREFIX/python_runner.py" <<'RUNNER'
import runpy
import sys
from pathlib import Path
from openroad import odb, utl
sys.modules["odb"] = odb
sys.modules["utl"] = utl
if len(sys.argv) < 2:
    raise SystemExit("usage: openroad-python SCRIPT.py [arguments]")
sys.argv = sys.argv[1:]
sys.path.insert(0, str(Path(sys.argv[0]).resolve().parent))
runpy.run_path(sys.argv[0], run_name="__main__")
RUNNER
chmod +x "$PREFIX/bin/openroad-python"
"$PREFIX/bin/openroad" -version | tee "$PREFIX/version.txt"
"$PREFIX/venv/bin/python" "$ROOT/openroad_python_smoke.py" | tee "$PREFIX/python-smoke.log"
"$PREFIX/bin/openroad-python" "$ROOT/openroad_python_smoke.py" | tee "$PREFIX/python-runner-smoke.log"
printf 'import odb, openroad, utl\nassert odb.dbDatabase.create() is not None\nprint("PASS: legacy imports")\n' > "$WORK/legacy_imports.py"
"$PREFIX/bin/openroad-python" "$WORK/legacy_imports.py" | tee "$PREFIX/legacy-imports.log"
printf 'OpenROAD=%s\nBazel=%s\n' "$REV" "$BAZEL_VERSION" > "$PREFIX/build-versions.txt"
cat > "$PREFIX/env.sh" <<EOF
module load python/3.11.11-5e66
export PATH="$PREFIX/bin:$PREFIX/venv/bin:\$PATH"
EOF
ln -s "$PREFIX" "$ROOT/.tools/openroad-new-$SLURM_JOB_ID"
mv -Tf "$ROOT/.tools/openroad-new-$SLURM_JOB_ID" "$ROOT/.tools/openroad"
printf 'exit_code=0\n' > "$PREFIX/verification-status.txt"
echo "PASS: installation and Python verification complete: $PREFIX"
