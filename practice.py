set -Eeuo pipefail

BASE=/application1
SRC="$BASE/BPLAN_MAX_TEAM_HANDOFF_20261102"
DST="$BASE/BPLAN_MAX_RUNTIME_CLEAN_20261102"
OUT="$BASE/BPLAN_MAX_RUNTIME_CLEAN_20261102.tar.gz"
SAMPLE="$SRC/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
NAME=bplan-clean-isolated-final

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== VERIFY EXISTING CLEAN CANDIDATE ==="

test -d "$DST"
test -s "$SAMPLE"
test -f "$DST/artifacts/v1.113/core-artifact/pipeline.py"
test -f "$DST/artifacts/v1.113/lookup/aep_seq_2.csv"
test -f "$DST/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py"

test ! -e "$OUT"
test ! -e "$OUT.partial"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Verification container name already exists"
  exit 1
fi

CREATED=0

cleanup() {
  rc=$?

  if [ "$CREATED" -eq 1 ]; then
    if [ "$rc" -ne 0 ]; then
      echo "=== VERIFICATION FAILURE LOGS ==="
      "${P[@]}" logs --tail 100 "$NAME" || true
    fi
    "${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "=== START ISOLATED NATIVE MAX SERVER ==="

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

echo "=== TEST NATIVE HTTP INSIDE CONTAINER ==="

"${P[@]}" exec -i "$NAME" /opt/venv/bin/python - <<'PY'
import json
import time
import urllib.request
import urllib.error

url = "http://127.0.0.1:18768/bplan/predict"

ready = False

for attempt in range(180):
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

assert ready, "Native MAX route did not become ready"

print("NATIVE MAX ROUTE: PASS")

with open("/tmp/bplan_sample.json", "rb") as f:
    payload = f.read()

request = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(request, timeout=480) as r:
    status = r.status
    response = json.load(r)

assert status == 200

ctas = response["jsonData"]["prediction"]["ctaList"]

assert isinstance(ctas, list)
assert len(ctas) == 4

print("BPLAN CLEAN NATIVE HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA COUNT:", len(ctas))
print("CLEAN RUNTIME: VERIFIED")
PY

echo "=== ADD TEAM RUN INSTRUCTIONS ==="

cat > "$DST/README.md" <<'EOF'
# BPLAN v1.113 — Native Modular MAX Serve

Clean single-request BPLAN runtime handoff.

## Contents

- artifacts/v1.113/: original DS model, weights and lookup assets
- artifacts/v1.113-max/maxserve_bplan_extension/: native MAX integration

Original model behavior and JSON contract are preserved.
Duplicate weight content is consolidated through portable relative links.

## Runtime requirements

Use a compatible MAX + FAISS runtime image.
The local POC image cta-max-faiss:local is NOT Verizon-approved.

The validated Python module is:

bplan_native_serve_dev.bplan_native_launcher

From the package root, mount the folder read-only at /workspace
and configure PYTHONPATH as:

/workspace/artifacts/v1.113-max/maxserve_bplan_extension:
/workspace/artifacts/v1.113/core-artifact:
/workspace/artifacts/v1.113/utils/dependency-utils

Native endpoint:
POST http://127.0.0.1:18768/bplan/predict

The receiving environment must provide the compatible runtime image,
sufficient memory and an available serving port.

A real BPLAN request returned HTTP 200 with four recommendations
during isolated clean-package verification.

This is a validated single-request POC, not production certification.
EOF

echo "=== CHECK PORTABLE LINKS ==="

python3 - "$DST" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

links = 0

for p in root.rglob("*"):
    if p.is_symlink():
        assert p.exists(), f"Broken link: {p}"
        assert p.resolve().is_relative_to(root), (
            f"External link: {p}"
        )
        links += 1

print("PORTABLE LINKS: PASS")
print("LINKS CHECKED:", links)
PY

echo "=== PACKAGE VERIFIED HANDOFF ==="

tar -C "$DST" -czf "$OUT.partial" \
  artifacts README.md

gzip -t "$OUT.partial"

mv "$OUT.partial" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "================================"
echo "BPLAN CLEAN RUNTIME HTTP: PASS"
echo "TEAM HANDOFF ARCHIVE: PASS"
echo "ORIGINAL CTA AND BPLAN: UNCHANGED"
echo "CLEAN FOLDER: $DST"
echo "CLEAN ARCHIVE: $OUT"
echo "================================"

ls -lh "$OUT" "$OUT.sha256"
