ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

date -u
curl --max-time 45 -sS \
  -o "$ROOT/clean_http_result.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== FRESH ERRORS ==="
$PODMAN logs --timestamps --since 1m --tail 35 cta-clean-native-batch2 2>&1
