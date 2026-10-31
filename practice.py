curl --max-time 120 -sS \
  -o /application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/clean_http_result.json \
  -w 'HTTP_STATUS:%{http_code}\n' \
  -X POST http://127.0.0.1:18767/v2/cta/predict \
  -H 'Content-Type: application/json' \
  --data-binary @/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
