curl --noproxy '*' -sS --fail \
  --max-time 240 \
  -X POST http://127.0.0.1:8765/v2/cta/predict \
  -H "Content-Type: application/json" \
  --data-binary @/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json \
  | python3 -c 'import json,sys; r=json.load(sys.stdin); assert isinstance(r.get("jsonData",{}).get("prediction"),dict); print("CTA JSON RESPONSE: PASS"); print("PREDICTION KEYS:",list(r["jsonData"]["prediction"]))'
