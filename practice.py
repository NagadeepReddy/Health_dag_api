set -euo pipefail

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
NAME=bplan-fresh-handoff-proof
RESPONSE=/application1/bplan_fresh_handoff_response.json
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== RESTORE BPLAN LOOKUP DATA ==="
test -f "$ROOT/artifacts/v1.113/lookup/page_seq_2.csv"
test -f "$STAGE/artifacts/v1.113/config/tokenizer_config.json"

mkdir -p "$STAGE/artifacts/v1.113"
cp -a "$ROOT/artifacts/v1.113/lookup" "$STAGE/artifacts/v1.113/"

test -f "$STAGE/artifacts/v1.113/lookup/page_seq_2.csv"
echo "BPLAN TOKENIZER + LOOKUP FILES: PASS"

echo "=== RESTART ISOLATED NATIVE SERVER ==="
"${P[@]}" rm -f "$NAME" 2>/dev/null || true

"${P[@]}" run -d --name "$NAME" --pull=never \
  --network=bridge -p 127.0.0.1:18769:18768 \
  -v "$STAGE:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

echo "=== CHECK SERVER ==="
READY=0

for i in $(seq 1 120); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18769/bplan/predict || true)

  if [ "$STATUS" = "405" ]; then
    READY=1
    break
  fi

  if [ "$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME")" != "true" ]; then
    break
  fi

  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "FRESH SERVER: NOT READY"
  "${P[@]}" logs --tail 80 "$NAME"
  exit 1
fi

echo "=== FRESH-CONTAINER REAL REQUEST ==="
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
assert isinstance(prediction.get("ctaList"), list)
assert prediction["ctaList"]

print("BPLAN FRESH-CONTAINER NATIVE HTTP: PASS")
print("PREDICTION KEYS:", sorted(prediction))
PY
