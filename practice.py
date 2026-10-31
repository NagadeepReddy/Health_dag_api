ROOT=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

curl --max-time 120 -sS \
  -o "$ROOT/clean_http_result.json" \
  -w '\nHTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"

head -c 600 "$ROOT/clean_http_result.json"
echo
