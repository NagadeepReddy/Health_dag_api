ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CLEAN NATIVE HTTP ==="
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl --max-time 180 -sS \
  -o "$ROOT/clean_http_final.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== CTA RESPONSE ==="
if test -s "$ROOT/clean_http_final.json"; then
  head -c 500 "$ROOT/clean_http_final.json"
  echo
fi

echo "=== FRESH WORKER ERRORS ==="
$PODMAN logs --since "$START" --tail 150 \
  cta-clean-native-batch2 2>&1 |
  grep -E 'FileNotFoundError|AssertionError|CTA PREDICT EXCEPTION|CTA RESPONSE' |
  tail -15
