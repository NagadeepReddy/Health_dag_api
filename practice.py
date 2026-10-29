bash <<'SH'
set -euo pipefail

R=/application1
REPO=$R/sajjna8/rt-pzaas-cta-offers-v1
RELEASE=$R/cta_max_native_release_candidate_20261028
NAME=cta-queue-bridge-test
LOG=$R/cta_queue_bridge_live.log
OUT=$R/cta_queue_bridge_response.json
INPUT=$REPO/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -s "$INPUT"
test -f "$RELEASE/cta_native_launcher.py"
test -f "$REPO/artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Test container name already exists"
  exit 1
fi

cleanup() {
  "${P[@]}" logs "$NAME" > "$LOG" 2>&1 || true
  "${P[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${P[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "=== RELEVANT SERVER LOG ==="
  grep -Ei 'CTA|queue|worker|error|exception|traceback|type|server ready' "$LOG" | tail -35 || true
}
trap cleanup EXIT

echo "STARTING REAL NATIVE MAX SERVE"

"${P[@]}" run -d \
  --name "$NAME" \
  --network bridge \
  -p 127.0.0.1:18080:8000 \
  --memory 12g --memory-swap 12g \
  --cpus 2 --pids-limit 128 \
  --read-only \
  --tmpfs /tmp:rw,size=1g,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e TMPDIR=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'API_TYPES=["openai","sagemaker","kserve"]' \
  -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace \
  -v "$REPO:/workspace:ro" \
  -v "$RELEASE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --devices cpu \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --weight-path /workspace/artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors \
  --quantization-encoding float32 \
  --port 8000 >/dev/null

READY=0
for i in $(seq 1 75); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18080/health || true)

  if [ "$STATUS" = 200 ]; then
    READY=1
    break
  fi

  if [ "$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)" != true ]; then
    break
  fi
  sleep 2
done

if [ "$READY" != 1 ]; then
  echo "NATIVE STARTUP: FAILED"
  exit 1
fi

echo "NATIVE SERVER: READY"
echo "SENDING ONE REAL CTA JSON REQUEST"

HTTP=$(curl -sS --max-time 210 \
  -o "$OUT" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$INPUT" \
  http://127.0.0.1:18080/v2/cta/predict) || HTTP=000

echo "REAL CTA HTTP STATUS: $HTTP"

python3 -S -B - "$OUT" "$HTTP" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
if not p.is_file():
    print("REAL NATIVE E2E: FAIL - No response")
    raise SystemExit(1)

try:
    response = json.loads(p.read_text())
except ValueError:
    print("REAL NATIVE E2E: FAIL - Invalid JSON")
    print(p.read_text()[:400])
    raise SystemExit(1)

data = response.get("jsonData", response) if isinstance(response, dict) else {}

valid = (
    sys.argv[2] == "200"
    and isinstance(data, dict)
    and isinstance(data.get("prediction"), dict)
    and isinstance(data["prediction"].get("offerList"), list)
)

print("RESPONSE SAMPLE:", str(response)[:450])
print("REAL NATIVE CTA E2E:", "PASS" if valid else "FAIL")

if not valid:
    raise SystemExit(1)
PY
SH
