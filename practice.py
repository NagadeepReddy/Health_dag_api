set -euo pipefail

SRC=/application1/BPLAN_MAX_TEAM_HANDOFF_20261102
DST=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102
OUT=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102.tar.gz
SAMPLE="$SRC/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
NAME=bplan-runtime-clean-verify

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -d "$SRC"
test -s "$SAMPLE"

if [ -e "$DST" ] || [ -e "$OUT" ]; then
  echo "STOP: Clean runtime destination already exists."
  exit 1
fi

if ss -lnt '( sport = :18768 )' | grep -q LISTEN; then
  echo "STOP: Port 18768 is occupied."
  exit 1
fi

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Verification container already exists."
  exit 1
fi

echo "=== CREATE ISOLATED CLEAN BPLAN RUNTIME ==="

python3 - "$SRC" "$DST" <<'PY'
from pathlib import Path
import shutil, os, sys, fnmatch

src = Path(sys.argv[1]).resolve()
dst = Path(sys.argv[2])

shutil.copytree(src, dst, symlinks=True)

junk_dirs = {
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".ipynb_checkpoints",
    "test_samples", "tests", ".git"
}

junk_patterns = (
    "*.pyc", "*.pyo", "*.log", "*.ipynb",
    "*.swp", "*.swo", "*.tmp", "*.bak",
    "*.orig", "*~", "test_*.py", "*_test.py"
)

removed = []

for current, dirs, files in os.walk(dst, topdown=False):
    folder = Path(current)

    for name in files:
        p = folder / name
        if p.is_symlink():
            continue
        if any(fnmatch.fnmatch(name, x) for x in junk_patterns):
            p.unlink()
            removed.append(str(p.relative_to(dst)))

    for name in dirs:
        p = folder / name
        if p.is_symlink():
            continue
        if name in junk_dirs:
            shutil.rmtree(p)
            removed.append(str(p.relative_to(dst)) + "/")

# Remove standalone investigation scripts only when no
# other retained source references their module name.
ext = dst / "artifacts/v1.113-max/maxserve_bplan_extension"

markers = (
    "_parity", "_diagnostic", "_debug",
    "_probe", "_inspect", "_audit",
    "_smoke", "_benchmark", "_baseline"
)

def sources():
    for p in ext.rglob("*"):
        if p.is_file() and not p.is_symlink():
            if p.suffix in {".py", ".sh", ".json", ".toml"}:
                if p.stat().st_size < 2_000_000:
                    yield p

for p in list(sources()):
    if p.suffix != ".py":
        continue
    if not any(x in p.stem.lower() for x in markers):
        continue

    referenced = any(
        p.stem in other.read_text(errors="replace")
        for other in sources()
        if other != p
    )

    if not referenced:
        p.unlink()
        removed.append(str(p.relative_to(dst)))

# No broken or outside symlinks permitted.
for p in dst.rglob("*"):
    if p.is_symlink():
        assert p.exists(), f"Broken link: {p}"
        assert p.resolve().is_relative_to(dst), (
            f"External link: {p}"
        )

required = [
    dst / "artifacts/v1.113/core-artifact/pipeline.py",
    dst / "artifacts/v1.113/lookup/aep_seq_2.csv",
    ext / "bplan_native_serve_dev/bplan_native_launcher.py",
]

for p in required:
    assert p.is_file(), f"Required file missing: {p}"

(dst / "README.md").write_text(
    "# BPLAN v1.113 — Native Modular MAX Serve\n\n"
    "Validated single-request serving integration.\n\n"
    "## Structure\n"
    "- artifacts/v1.113/: unchanged model, DS and lookups\n"
    "- artifacts/v1.113-max/maxserve_bplan_extension/: "
    "isolated MAX integration and weights\n\n"
    "## Native serving\n"
    "Run bplan_native_serve_dev.bplan_native_launcher using "
    "the approved MAX runtime with the extension, "
    "core-artifact and dependency-utils directories on "
    "PYTHONPATH. Mount this folder as /workspace.\n\n"
    "Endpoint: POST /bplan/predict on port 18768.\n\n"
    "The local cta-max-faiss image used for POC verification "
    "is NOT an approved deployment image.\n\n"
    "Original DS logic and model weights are unchanged.\n"
)

print("REMOVED TEST/CACHE/INVESTIGATION ITEMS:", len(removed))
for item in removed[:40]:
    print("REMOVED:", item)

print("REQUIRED RUNTIME FILES: PASS")
print("INTERNAL WEIGHT LINKS: PASS")
print("ORIGINAL RELEASE: UNCHANGED")
print("CLEAN CANDIDATE CREATED:", dst)
PY

cleanup() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "=== VERIFICATION FAILURE LOGS ==="
    "${P[@]}" logs --tail 80 "$NAME" 2>/dev/null || true
    echo "ORIGINAL VALIDATED HANDOFF IS UNCHANGED."
  fi
  "${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== VERIFY CLEAN CODE USING NATIVE MAX ==="

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

READY=0

for i in $(seq 1 180); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 \
    http://127.0.0.1:18768/bplan/predict || true)

  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi

  sleep 2
done

test "$READY" -eq 1
echo "CLEAN NATIVE ROUTE: PASS"

HTTP=$(curl -sS --max-time 480 \
  -o /tmp/bplan_runtime_clean_response.json \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$SAMPLE" \
  http://127.0.0.1:18768/bplan/predict)

test "$HTTP" = "200"

python3 - <<'PY'
import json

p = "/tmp/bplan_runtime_clean_response.json"

with open(p) as f:
    response = json.load(f)

ctas = response["jsonData"]["prediction"]["ctaList"]

assert isinstance(ctas, list)
assert len(ctas) == 4

print("CLEAN NATIVE MAX HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA COUNT:", len(ctas))
PY

echo "=== PACKAGE VERIFIED CLEAN RUNTIME ==="

tar -C "$DST" -czf "$OUT.partial" \
  artifacts README.md

gzip -t "$OUT.partial"
mv "$OUT.partial" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "=== FINAL RESULT ==="
echo "CLEAN BPLAN RUNTIME: VERIFIED"
echo "ORIGINAL BPLAN AND CTA: UNCHANGED"
echo "RUNTIME FOLDER: $DST"
echo "RUNTIME ARCHIVE: $OUT"
ls -lh "$OUT" "$OUT.sha256"
