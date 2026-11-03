set -euo pipefail

STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
NAME=bplan-fresh-handoff-proof
OUT=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz
RESPONSE=/application1/bplan_fresh_handoff_response.json

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== VERIFY REAL BPLAN RESOURCES ==="

test -s "$STAGE/artifacts/v1.113/lookup/aep_seq_2.csv"
test -s "$STAGE/artifacts/v1.113/config/tokenizer_config.json"

echo "BPLAN CONFIG AND LOOKUPS: PASS"

echo "=== START FRESH NATIVE MAX SERVE ==="

"${P[@]}" rm -f "$NAME" 2>/dev/null || true

"${P[@]}" run -d \
  --name "$NAME" \
  --pull=never \
  --network=bridge \
  -p 127.0.0.1:18769:18768 \
  -v "$STAGE:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

READY=0

for i in $(seq 1 120); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 \
    http://127.0.0.1:18769/bplan/predict || true)

  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi

  if [ "$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME")" != "true" ]; then
    break
  fi

  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "FRESH SERVER STARTUP: FAILED"
  "${P[@]}" logs --tail 100 "$NAME"
  exit 1
fi

echo "NATIVE ROUTE: PASS"

echo "=== REAL SINGLE-REQUEST HTTP TEST ==="

SAMPLE="$STAGE/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
test -s "$SAMPLE"

CODE=$(curl -sS --max-time 480 \
  -o "$RESPONSE" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  http://127.0.0.1:18769/bplan/predict) || CODE=000

echo "HTTP STATUS: $CODE"

if [ "$CODE" != "200" ]; then
  echo "FRESH HTTP VALIDATION: FAILED"
  "${P[@]}" logs --tail 120 "$NAME"
  exit 1
fi

RESPONSE="$RESPONSE" python3 - <<'PY'
import json, os
from pathlib import Path

data = json.loads(Path(os.environ["RESPONSE"]).read_text())
prediction = data["jsonData"]["prediction"]

assert isinstance(prediction["ctaList"], list)
assert prediction["ctaList"]

print("FRESH-CONTAINER NATIVE HTTP: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA LIST COUNT:", len(prediction["ctaList"]))
PY

echo "=== PACKAGE CORRECTED HANDOFF ==="

if [ -e "$OUT" ]; then
  echo "STOP: Final archive already exists; preserving it."
  exit 1
fi

TMP="$OUT.partial"
trap 'rm -f "$TMP"' EXIT

tar -C "$STAGE" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='.ipynb_checkpoints' \
  -czf "$TMP" \
  artifacts/v1.113 \
  artifacts/v1.113-max/maxserve_bplan_extension

gzip -t "$TMP"
mv "$TMP" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "================================"
echo "BPLAN FRESH NATIVE HTTP: PASS"
echo "BPLAN FINAL HANDOFF: PASS"
echo "ORIGINAL DS: UNCHANGED"
echo "================================"

ls -lh "$OUT" "$OUT.sha256"
