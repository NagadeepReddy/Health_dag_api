set -euo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
NAME=bplan-fresh-handoff-proof
OUT=/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz
RESPONSE=/application1/bplan_fresh_handoff_response.json
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== RESTORE MISSING TOKENIZER CONFIG ==="
test -d "$ROOT/artifacts/v1.113/config"
mkdir -p "$STAGE/artifacts/v1.113"

if [ ! -d "$STAGE/artifacts/v1.113/config" ]; then
  cp -a "$ROOT/artifacts/v1.113/config" "$STAGE/artifacts/v1.113/"
fi

test -f "$STAGE/artifacts/v1.113/config/tokenizer_config.json"
echo "TOKENIZER CONFIG: PASS"

echo "=== START FRESH NATIVE MAX CONTAINER ==="
"${P[@]}" rm -f "$NAME" 2>/dev/null || true

"${P[@]}" run -d --name "$NAME" --pull=never \
  --network=bridge -p 127.0.0.1:18769:18768 \
  -v "$STAGE:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

READY=0
for i in $(seq 1 120); do
  HTTP=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 \
    http://127.0.0.1:18769/bplan/predict || true)

  if [ "$HTTP" = "405" ]; then
    READY=1
    break
  fi

  if [ "$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME")" != "true" ]; then
    break
  fi
  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "FRESH STARTUP: FAILED"
  "${P[@]}" logs --tail 90 "$NAME"
  exit 1
fi

echo "FRESH NATIVE ROUTE: PASS"

echo "=== REAL BPLAN REQUEST ==="
STATUS=$(curl -sS --max-time 360 \
  -o "$RESPONSE" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @"$STAGE/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json" \
  http://127.0.0.1:18769/bplan/predict) || STATUS=000

echo "HTTP STATUS: $STATUS"

if [ "$STATUS" != "200" ]; then
  "${P[@]}" logs --tail 100 "$NAME"
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
print("BPLAN JSON RESPONSE: PASS")
PY

echo "=== CREATE CORRECTED HANDOFF PACKAGE ==="
test ! -e "$OUT" || { echo "STOP: Final archive already exists"; exit 1; }

tar -C "$STAGE" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='.ipynb_checkpoints' \
  -czf "$OUT" \
  artifacts/v1.113/core-artifact \
  artifacts/v1.113/utils \
  artifacts/v1.113/config \
  artifacts/v1.113-max/maxserve_bplan_extension

gzip -t "$OUT"
sha256sum "$OUT" > "$OUT.sha256"

echo "BPLAN CORRECTED HANDOFF: PASS"
ls -lh "$OUT" "$OUT.sha256"
