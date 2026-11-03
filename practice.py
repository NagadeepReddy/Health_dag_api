set -euo pipefail

STAGE=/application1/BPLAN_MAX_TEAM_HANDOFF_20261102
SAMPLE="$STAGE/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
OUT=/tmp/bplan_team_final_response.json
NAME=bplan-team-final-check

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -s "$SAMPLE"
test -d "$STAGE/artifacts/v1.113-max/maxserve_bplan_extension"

if ss -lnt '( sport = :18768 )' | grep -q LISTEN; then
  echo "STOP: Port 18768 is already in use. Existing service preserved."
  exit 1
fi

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists. Nothing overwritten."
  exit 1
fi

cleanup() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "=== FAILURE DIAGNOSTICS ==="
    "${P[@]}" logs --tail 100 "$NAME" || true
  fi
  "${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== START FRESH BPLAN TEAM CONTAINER ==="

"${P[@]}" run -d \
  --name "$NAME" \
  --pull=never \
  --network=host \
  -v "$STAGE:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

echo "=== WAIT FOR NATIVE ROUTE ==="

READY=0
for i in $(seq 1 180); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 \
    http://127.0.0.1:18768/bplan/predict || true)

  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi
  sleep 1
done

test "$READY" -eq 1

echo "=== REAL BPLAN NATIVE HTTP TEST ==="

HTTP=$(curl -sS --max-time 480 \
  -o "$OUT" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$SAMPLE" \
  http://127.0.0.1:18768/bplan/predict)

echo "HTTP STATUS: $HTTP"
test "$HTTP" = "200"

python3 - "$OUT" <<'PY'
import json, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

assert isinstance(data, dict)
prediction = data["jsonData"]["prediction"]
assert isinstance(prediction, dict)
ctas = prediction["ctaList"]
assert isinstance(ctas, list)
assert len(ctas) == 4, f"Unexpected CTA count: {len(ctas)}"

print("NATIVE MAX HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA RECOMMENDATIONS:", len(ctas))
print("BPLAN CLEAN TEAM FOLDER: PASS")
print("BPLAN SINGLE-REQUEST POC: PASS")
PY
