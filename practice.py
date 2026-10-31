ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== CLEAN NATIVE HTTP ==="
curl --max-time 180 -sS \
  -o "$ROOT/clean_http_nlp_verified.json" \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

echo "=== RESPONSE ==="
if test -s "$ROOT/clean_http_nlp_verified.json"; then
  head -c 600 "$ROOT/clean_http_nlp_verified.json"
  echo
fi

echo "=== LATEST WORKER ERRORS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --since 4m --tail 100 \
  cta-clean-native-batch2 2>&1 |
  grep -E 'FileNotFoundError|AssertionError|CTA PREDICT EXCEPTION|CTA RESPONSE' |
  tail -12
