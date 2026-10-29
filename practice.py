bash <<'SH'
set -Eeuo pipefail

BASE=/application1
REPO=$BASE/sajjna8/rt-pzaas-cta-offers-v1
RELEASE=$BASE/cta_max_native_release_candidate_20261028
MODEL=$REPO/artifacts/v1.168-max/cta_native_model
TESTS=$REPO/artifacts/v1.168-max/test-results
INPUT=$TESTS/cta_max_tiles_smoketest_input.json
EXPECTED=$TESTS/cta_max_tiles_response.json
TORCH=$TESTS/cta_pytorch_tiles_response.json
OUT=$BASE/cta_native_tiles_parity_response.json
LOG=$BASE/cta_native_tiles_parity.log
NAME=cta-native-tiles-parity

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

for f in "$INPUT" "$EXPECTED" "$TORCH" \
         "$MODEL/cta_real_fp32.safetensors" \
         "$RELEASE/cta_native_launcher.py"; do
  test -s "$f" || { echo "STOP: Missing $f"; exit 1; }
done

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Test container name already exists"
  exit 1
fi

cleanup() {
  "${P[@]}" logs "$NAME" > "$LOG" 2>&1 || true
  "${P[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${P[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "SERVER LOG: $LOG"
  grep -E 'CTA PREDICT_RAW|CTA RESPONSE QUEUE SEND|CTA HTTP QUEUE ITEM|Server ready|ERROR|Traceback' "$LOG" | tail -15 || true
}
trap cleanup EXIT

echo "STARTING BUILT-IN MAX SERVE FOR SAME-INPUT PARITY"

"${P[@]}" run -d \
  --name "$NAME" \
  --network bridge \
  -p 127.0.0.1:18081:8000 \
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
for i in $(seq 1 90); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18081/health || true)

  if [ "$STATUS" = 200 ]; then
    READY=1
    break
  fi

  RUNNING=$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)
  if [ "$RUNNING" != true ]; then
    echo "STOP: Native server exited"
    exit 1
  fi
  sleep 2
done

test "$READY" = 1 || { echo "STOP: Server not ready"; exit 1; }

echo "SENDING EXACT SAVED TILES BASELINE INPUT"

HTTP=$(curl -sS --max-time 320 \
  -o "$OUT" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$INPUT" \
  http://127.0.0.1:18081/v2/cta/predict) || HTTP=000

echo "NATIVE HTTP STATUS: $HTTP"

python3 -S -B - "$OUT" "$EXPECTED" "$TORCH" "$HTTP" <<'PY'
import json, sys
from pathlib import Path

native_path, max_path, torch_path = map(Path, sys.argv[1:4])
status = sys.argv[4]

def prediction(path):
    data = json.loads(path.read_text())
    data = data.get("jsonData", data)
    return data["prediction"]

assert native_path.is_file(), "Native response missing"
assert status == "200", f"Native HTTP failed: {status}"

native = prediction(native_path)
baseline = prediction(max_path)
torch = prediction(torch_path)

assert isinstance(native.get("offerList"), list)

print("=== EXACT SAME-INPUT BUSINESS PARITY ===")
print("NATIVE OFFERS:", len(native["offerList"]))
print("MAX BASELINE OFFERS:", len(baseline["offerList"]))
print("PYTORCH BASELINE OFFERS:", len(torch["offerList"]))
print("PYTORCH VS MAX:", "MATCH" if torch == baseline else "DIFFERENT")
print("NATIVE VS MAX OFFERS:",
      "MATCH" if native["offerList"] == baseline["offerList"] else "DIFFERENT")
print("NATIVE VS MAX FULL PREDICTION:",
      "MATCH" if native == baseline else "DIFFERENT")
print("RESPONSE FILE:", native_path)
print("DS CODE: NOT MODIFIED BY THIS TEST")

if native != baseline:
    raise SystemExit("BUSINESS PARITY: NOT YET PROVEN")

print("BUSINESS PARITY: PASS")
PY
SH
