curl --max-time 60 -sS -w '\nHTTP_STATUS:%{http_code}\n' \
  -X POST 'http://127.0.0.1:18767/v2/cta/predict' \
  -H 'Content-Type: application/json' \
  --data-binary @/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
