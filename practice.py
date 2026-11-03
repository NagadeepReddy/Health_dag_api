set -Eeuo pipefail

SRC=/application1/BPLAN_MAX_TEAM_HANDOFF_20261102
DST=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102
OUT=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102.tar.gz
SAMPLE="$SRC/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
NAME=bplan-runtime-clean-proof
PORT=18768

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -d "$SRC" || { echo "ERROR: Validated handoff missing"; exit 1; }
test -s "$SAMPLE" || { echo "ERROR: Original test input missing"; exit 1; }
test ! -e "$DST" || { echo "STOP: Destination already exists"; exit 1; }
test ! -e "$OUT" || { echo "STOP: Archive already exists"; exit 1; }

echo "=== CREATE MISSING CLEAN CANDIDATE ==="

python3 - "$SRC" "$DST" <<'PY'
from pathlib import Path
import shutil, os, sys, fnmatch

src = Path(sys.argv[1]).resolve()
dst = Path(sys.argv[2])
shutil.copytree(src, dst, symlinks=True)

removed = []

junk_dirs = {
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".ipynb_checkpoints", ".git",
    "tests", "test_samples"
}
junk_files = (
    "*.pyc", "*.pyo", "*.log", "*.swp", "*.swo",
    "*.tmp", "*.bak", "*.orig", "*.ipynb", "*~",
    "test_*.py", "*_test.py"
)

for current, dirs, files in os.walk(dst, topdown=False):
    folder = Path(current)
    for name in files:
        p = folder / name
        if not p.is_symlink() and any(
            fnmatch.fnmatch(name, x) for x in junk_files
        ):
            p.unlink()
            removed.append(str(p.relative_to(dst)))
    for name in dirs:
        p = folder / name
        if p.is_dir() and not p.is_symlink() and name in junk_dirs:
            shutil.rmtree(p)
            removed.append(str(p.relative_to(dst)) + "/")

required = [
    "artifacts/v1.113/core-artifact/pipeline.py",
    "artifacts/v1.113/lookup/aep_seq_2.csv",
    "artifacts/v1.113-max/maxserve_bplan_extension/"
    "bplan_native_serve_dev/bplan_native_launcher.py"
]

for name in required:
    assert (dst / name).is_file(), f"Missing required file: {name}"

for p in dst.rglob("*"):
    if p.is_symlink():
        assert p.exists(), f"Broken symlink: {p}"
        assert p.resolve().is_relative_to(dst.resolve()), (
            f"External dependency: {p}"
        )

print("CLEAN FOLDER: CREATED")
print("TEST/CACHE ITEMS REMOVED:", len(removed))
print("REQUIRED FILES: PASS")
print("PORTABLE WEIGHT LINKS: PASS")
print("ORIGINAL RELEASE: UNCHANGED")
PY

echo "=== CHECK VERIFICATION RESOURCES ==="

if ss -lnt "( sport = :$PORT )" | grep -q LISTEN; then
    echo "STOP: Port 18768 occupied; existing service preserved"
    exit 1
fi

if "${P[@]}" container exists "$NAME"; then
    echo "STOP: Existing proof container preserved"
    exit 1
fi

CREATED=0
cleanup() {
    rc=$?
    if [ "$CREATED" -eq 1 ]; then
        if [ "$rc" -ne 0 ]; then
            "${P[@]}" logs --tail 80 "$NAME" || true
        fi
        "${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

echo "=== START NATIVE MAX FROM CLEAN FOLDER ==="

"${P[@]}" run -d \
    --name "$NAME" \
    --pull=never \
    --network=host \
    -v "$DST:/workspace:ro" \
    -w /workspace \
    -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -m bplan_native_serve_dev.bplan_native_launcher

CREATED=1

READY=0
for i in $(seq 1 180); do
    CODE=$(curl -s --max-time 2 -o /dev/null \
        -w '%{http_code}' \
        http://127.0.0.1:18768/bplan/predict || true)
    if [ "$CODE" = 405 ]; then
        READY=1
        break
    fi
    sleep 2
done

test "$READY" -eq 1 || {
    echo "NATIVE STARTUP: FAILED"
    exit 1
}

HTTP=$(curl -sS --max-time 480 \
    -o /tmp/bplan_runtime_clean_response.json \
    -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    --data-binary "@$SAMPLE" \
    http://127.0.0.1:18768/bplan/predict)

test "$HTTP" = 200

python3 - <<'PY'
import json
with open("/tmp/bplan_runtime_clean_response.json") as f:
    data = json.load(f)
ctas = data["jsonData"]["prediction"]["ctaList"]
assert isinstance(ctas, list) and len(ctas) == 4
print("CLEAN NATIVE MAX HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
PY

echo "=== PACKAGE VERIFIED CLEAN FOLDER ==="

tar -C "$DST" -czf "$OUT.partial" artifacts
gzip -t "$OUT.partial"
mv "$OUT.partial" "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "BPLAN CLEAN RUNTIME: VERIFIED"
echo "ORIGINAL CTA AND BPLAN: UNCHANGED"
echo "FOLDER: $DST"
echo "ARCHIVE: $OUT"
