bash <<'SH'
set -euo pipefail

ROOT=/application1
REPO=$ROOT/sajjna8/rt-pzaas-cta-offers-v1
RELEASE=$ROOT/cta_max_native_release_candidate_20261028
MODEL=$REPO/artifacts/v1.168-max/cta_native_model
INPUT=$REPO/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
IMAGE=localhost/cta-max-faiss:local
NAME=cta-kserve-final-test
LOG=$ROOT/cta_kserve_final_test.log
SCHEMA=$ROOT/cta_kserve_routes.json
OUT=$ROOT/cta_kserve_response.json

PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -s "$INPUT"
test -s "$MODEL/cta_real_fp32.safetensors"
test -f "$RELEASE/cta_native_launcher.py"

if "${PODMAN[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

cleanup() {
  "${PODMAN[@]}" logs "$NAME" > "$LOG" 2>&1 || true
  "${PODMAN[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${PODMAN[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "=== FINAL LOG ==="
  tail -25 "$LOG"
}
trap cleanup EXIT

echo "STARTING NATIVE MAX WITH KSERVE ENABLED"

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
  -e 'API_TYPES=["openai","sagemaker","kserve"]' \
  -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' \
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

for i in $(seq 1 75); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18080/health || true)

  if [ "$STATUS" = 200 ]; then
    READY=1
    break
  fi

  if [ "$("${PODMAN[@]}" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)" != true ]; then
    break
  fi

  sleep 2
done

if [ "$READY" != 1 ]; then
  echo "SERVER NOT READY"
  exit 1
fi

echo "NATIVE SERVER: READY"

curl -fsS --max-time 10 \
  http://127.0.0.1:18080/openapi.json \
  -o "$SCHEMA"

ROUTE=$(python3 -S -B - "$SCHEMA" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    paths = json.load(f)["paths"]

matches = [
    p for p, methods in paths.items()
    if p.endswith("/cta/predict") and "post" in methods
]

print(matches[0] if len(matches) == 1 else "")
PY
)

if [ -z "$ROUTE" ]; then
  echo "STOP: CTA PREDICT ROUTE NOT EXPOSED"
  exit 1
fi

echo "CTA ROUTE REGISTERED: $ROUTE"
echo "SENDING REAL CTA JSON"

HTTP=$(curl -sS --max-time 210 \
  -o "$OUT" \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$INPUT" \
  "http://127.0.0.1:18080$ROUTE")

echo "CTA HTTP STATUS: $HTTP"

python3 -S -B - "$OUT" "$HTTP" <<'PY'
import json, sys

with open(sys.argv[1]) as f:
    result = json.load(f)

data = result.get("jsonData", result) if isinstance(result, dict) else {}

print("RESPONSE KEYS:", list(result) if isinstance(result, dict) else type(result).__name__)
valid = (
    sys.argv[2] == "200"
    and isinstance(data, dict)
    and isinstance(data.get("prediction"), dict)
    and isinstance(data["prediction"].get("offerList"), list)
)

print("REAL NATIVE CTA E2E:", "PASS" if valid else "NOT PASSED")
if not valid:
    print("RESPONSE SAMPLE:", str(result)[:600])
    raise SystemExit(1)
PY
SH
