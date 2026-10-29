bash <<'SH'
set -euo pipefail

ROOT=/application1
REPO=$ROOT/sajjna8/rt-pzaas-cta-offers-v1
RELEASE=$ROOT/cta_max_native_release_candidate_20261028
MODEL=$REPO/artifacts/v1.168-max/cta_native_model
INPUT=$REPO/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
IMAGE=localhost/cta-max-faiss:local
NAME=cta-final-native-smoke
LOG=$ROOT/cta_native_faiss_live_test.log
OUT=$ROOT/cta_native_faiss_response.json

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -f "$RELEASE/cta_native_launcher.py"
test -s "$MODEL/cta_real_fp32.safetensors"
test -s "$INPUT"

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

cleanup() {
  "${PODMAN[@]}" logs "$NAME" >"$LOG" 2>&1 || true
  "${PODMAN[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${PODMAN[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "=== FINAL NATIVE LOG ==="
  tail -35 "$LOG"
}
trap cleanup EXIT

echo "STARTING REAL NATIVE MAX SERVE WITH FAISS"

"${PODMAN[@]}" run -d \
  --name "$NAME" \
  --network bridge \
  -p 127.0.0.1:18080:8000 \
  --memory 12g \
  --memory-swap 12g \
  --cpus 2 \
  --pids-limit 128 \
  --read-only \
  --tmpfs /tmp:rw,size=1g,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e TMPDIR=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace \
  -v "$REPO:/workspace:ro" \
  -v "$RELEASE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --devices cpu \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --weight-path /workspace/artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors \
  --quantization-encoding float32 \
  --port 8000 >/dev/null

READY=0
for i in $(seq 1 40); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18080/health || true)

  if [ "$STATUS" = 200 ]; then
    READY=1
    break
  fi

  if [ "$("${PODMAN[@]}" inspect -f '{{.State.Running}}' "$NAME")" != true ]; then
    break
  fi

  sleep 3
done

if [ "$READY" != 1 ]; then
  echo "STANDALONE SERVER: NOT READY"
  exit 1
fi

echo "STANDALONE SERVER: READY"
echo "SENDING REAL CTA JSON"

curl -sS --max-time 200 \
  -o "$OUT" \
  -w 'HTTP STATUS: %{http_code}\nLATENCY SECONDS: %{time_total}\n' \
  -H 'Content-Type: application/json' \
  --data-binary "@$INPUT" \
  http://127.0.0.1:18080/v2/cta/predict

python3 -S -B - "$OUT" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    result = json.load(f)
print("RESPONSE KEYS:", list(result) if isinstance(result, dict) else type(result).__name__)
if isinstance(result, dict):
    data = result.get("jsonData", result)
    if isinstance(data, dict):
        print("PREDICTION PRESENT:", "prediction" in data)
PY
SH
