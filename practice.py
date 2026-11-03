set -Eeuo pipefail

BASE=/application1
SRC="$BASE/BPLAN_MAX_RUNTIME_CLEAN_20261102"
DST="$BASE/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102"
OUT="$BASE/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102.tar.gz"
SAMPLE="$BASE/BPLAN_MAX_TEAM_HANDOFF_20261102/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
NAME=bplan-final-handoff-proof

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -d "$SRC"
test -s "$SAMPLE"
test ! -e "$DST"
test ! -e "$OUT"
test ! -e "$OUT.partial"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Verification container already exists"
  exit 1
fi

echo "=== CREATE FINAL ISOLATED COPY ==="

cp -a --reflink=auto "$SRC" "$DST"

python3 - "$DST" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

candidates = [
    ext / "bplan_max_projection_parity.py",
    ext / "cta_reference/cta_worker_adapter.py",
]

sources = [
    p for p in root.rglob("*")
    if p.is_file()
    and p.suffix in {".py", ".sh", ".json", ".yaml", ".yml", ".toml"}
    and p.stat().st_size < 2000000
]

contents = {
    p: p.read_text(errors="replace")
    for p in sources
}

for p in candidates:
    assert p.is_file(), f"Expected cleanup candidate missing: {p}"

    names = [p.stem]
    if p.name == "cta_worker_adapter.py":
        names += ["CTAWorkerAdapter", "cta_reference"]

    refs = [
        str(q.relative_to(root))
        for q, content in contents.items()
        if q != p and any(name in content for name in names)
    ]

    assert not refs, f"Referenced module {p.name}: {refs}"

for p in candidates:
    p.unlink()
    print("REMOVED:", p.relative_to(root))

refdir = ext / "cta_reference"
if refdir.is_dir():
    remaining = list(refdir.iterdir())
    if all(p.name == "__init__.py" for p in remaining):
        for p in remaining:
            p.unlink()
        refdir.rmdir()
        print("REMOVED: unused CTA reference package")

audit = ext / "bplan_max_full_dependency_audit.json"
if audit.exists():
    audit.unlink()
    print("REMOVED: development audit report")

required = [
    root / "artifacts/v1.113/core-artifact/pipeline.py",
    root / "artifacts/v1.113/lookup/aep_seq_2.csv",
    ext / "bplan_native_serve_dev/bplan_native_launcher.py",
]

for p in required:
    assert p.is_file(), f"Required file missing: {p}"

for p in root.rglob("*"):
    if p.is_symlink():
        assert p.exists(), f"Broken symlink: {p}"
        assert p.resolve().is_relative_to(root), (
            f"External dependency: {p}"
        )

print("REQUIRED FILES: PASS")
print("WEIGHT LINKS: PASS")
print("TARGETED DEVELOPMENT CLEANUP: PASS")
print("ORIGINAL RELEASES: UNCHANGED")
PY

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

echo "=== VERIFY NATIVE MAX IN ISOLATED CONTAINER ==="

"${P[@]}" run -d \
  --name "$NAME" \
  --pull=never \
  --network=none \
  -v "$DST:/workspace:ro" \
  -v "$SAMPLE:/tmp/bplan_sample.json:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

CREATED=1

"${P[@]}" exec -i "$NAME" /opt/venv/bin/python - <<'PY'
import json
import time
import urllib.request
import urllib.error

url = "http://127.0.0.1:18768/bplan/predict"

ready = False

for _ in range(180):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        status = None

    if status == 405:
        ready = True
        break

    time.sleep(2)

assert ready, "Native route failed to start"

with open("/tmp/bplan_sample.json", "rb") as f:
    payload = f.read()

request = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(request, timeout=480) as r:
    assert r.status == 200
    response = json.load(r)

ctas = response["jsonData"]["prediction"]["ctaList"]
assert isinstance(ctas, list) and len(ctas) == 4

print("FINAL NATIVE MAX HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA COUNT:", len(ctas))
PY

echo "=== PACKAGE FINAL HANDOFF ==="

tar -C "$DST" -czf "$OUT.partial" artifacts README.md
gzip -t "$OUT.partial"
mv "$OUT.partial" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "=============================="
echo "BPLAN FINAL CLEANUP: PASS"
echo "NATIVE MAX HTTP 200: PASS"
echo "TEAM HANDOFF: VERIFIED"
echo "ORIGINAL CTA/BPLAN: UNCHANGED"
echo "FINAL FOLDER: $DST"
echo "FINAL ARCHIVE: $OUT"
echo "=============================="
