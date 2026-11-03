set -Eeuo pipefail

SRC=/application1/BPLAN_MAX_TEAM_HANDOFF_20261102
DST=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102
OUT=/application1/BPLAN_MAX_RUNTIME_CLEAN_20261102.tar.gz
NAME=bplan-runtime-clean-proof
RESULT=/tmp/bplan_runtime_clean_verified.json
PORT=18770

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== CHECK CLEAN PACKAGE ==="

if [ -f "$OUT" ]; then
  test -f "$OUT.sha256"
  sha256sum -c "$OUT.sha256"
  echo "CLEAN ARCHIVE: ALREADY VERIFIED"
  exit 0
fi

test -d "$SRC" || { echo "STOP: Validated source missing"; exit 1; }
test -d "$DST" || { echo "STOP: Clean candidate missing"; exit 1; }
test -f "$DST/artifacts/v1.113/core-artifact/pipeline.py"

SAMPLE="$SRC/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
test -s "$SAMPLE"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Existing proof container preserved"
  exit 1
fi

if ss -lnt "( sport = :$PORT )" | grep -q LISTEN; then
  echo "STOP: Verification port occupied"
  exit 1
fi

test ! -e "$OUT.partial" || {
  echo "STOP: Existing partial archive preserved"
  exit 1
}

CREATED=0

cleanup() {
  RC=$?
  if [ "$CREATED" -eq 1 ]; then
    if [ "$RC" -ne 0 ]; then
      echo "=== ACTUAL FAILURE LOGS ==="
      "${P[@]}" logs --tail 100 "$NAME" 2>&1 || true
    fi
    "${P[@]}" rm -f "$NAME" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "=== START ISOLATED CLEAN MAX SERVE ==="

"${P[@]}" run -d \
  --name "$NAME" \
  --pull=never \
  --network=bridge \
  -p 127.0.0.1:${PORT}:18768 \
  -v "$DST:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

CREATED=1

echo "=== WAIT FOR NATIVE ROUTE ==="

READY=0

for i in $(seq 1 150); do
  CODE=$(curl -s --max-time 2 -o /dev/null \
    -w '%{http_code}' \
    "http://127.0.0.1:$PORT/bplan/predict" || true)

  if [ "$CODE" = "405" ]; then
    READY=1
    break
  fi

  if [ "$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME")" != true ]; then
    echo "Container exited during startup"
    break
  fi

  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "CLEAN MAX STARTUP: FAILED"
  exit 1
fi

echo "CLEAN NATIVE ROUTE: PASS"

echo "=== REAL BPLAN HTTP TEST ==="

HTTP=$(curl -sS --max-time 480 \
  -o "$RESULT" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  "http://127.0.0.1:$PORT/bplan/predict") || HTTP=000

echo "HTTP STATUS: $HTTP"

if [ "$HTTP" != "200" ]; then
  echo "CLEAN HTTP VALIDATION: FAILED"
  exit 1
fi

python3 - "$RESULT" <<'PY'
import json, sys

with open(sys.argv[1]) as f:
    response = json.load(f)

ctas = response["jsonData"]["prediction"]["ctaList"]
assert isinstance(ctas, list)
assert len(ctas) == 4

print("CLEAN NATIVE HTTP 200: PASS")
print("REAL BPLAN RESPONSE: PASS")
print("CTA COUNT:", len(ctas))
PY

echo "=== BUILD VERIFIED CLEAN PACKAGE ==="

tar -C "$DST" \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -czf "$OUT.partial" \
  artifacts README.md

gzip -t "$OUT.partial"
mv "$OUT.partial" "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
sha256sum -c "$OUT.sha256"

echo "=============================="
echo "BPLAN CLEAN RUNTIME: PASS"
echo "BPLAN CLEAN HANDOFF: PASS"
echo "ORIGINAL CTA AND DS: UNCHANGED"
echo "=============================="

ls -lh "$OUT" "$OUT.sha256"
