set -euo pipefail

STAGE=/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102
NAME=bplan-fresh-handoff-proof
OUT=/application1/bplan_fresh_handoff_response.json
SAMPLE="$STAGE/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -f "$SAMPLE"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Proof container already exists. Preserving it."
  exit 1
fi

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
  echo "FRESH CONTAINER STARTUP: NOT VERIFIED"
  "${P[@]}" logs --tail 100 "$NAME"
  exit 1
fi

echo "FRESH NATIVE ROUTE: PASS"

HTTP=$(curl -sS --max-time 360 \
  -o "$OUT" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  http://127.0.0.1:18769/bplan/predict) || HTTP=000

echo "FRESH CONTAINER HTTP: $HTTP"

if [ "$HTTP" != "200" ]; then
  "${P[@]}" logs --tail 100 "$NAME"
  exit 1
fi

OUT="$OUT" python3 - <<'PY'
import json, os
from pathlib import Path

data = json.loads(Path(os.environ["OUT"]).read_text())
prediction = data["jsonData"]["prediction"]
assert isinstance(prediction, dict)
assert prediction.get("ctaList") is not None

print("FRESH CONTAINER JSON RESPONSE: PASS")
print("PREDICTION KEYS:", sorted(prediction))
print("BPLAN PORTABLE HANDOFF NATIVE HTTP: PASS")
PY
