ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CLEAN HTTP ==="
curl --max-time 45 -sS \
  -o "$ROOT/clean_http_result.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== RESPONSE ==="
head -c 500 "$ROOT/clean_http_result.json"
echo

echo "=== LATEST WORKER LOGS ==="
$PODMAN logs --since 2m --tail 45 cta-clean-native-batch2 2>&1
