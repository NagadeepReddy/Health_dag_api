cd /application1/sajjna8/rt-pzaas-cta-offers-v1

curl -sS -i --max-time 120 \
  -X POST http://127.0.0.1:8000/v2/cta/predict \
  -H "Content-Type: application/json" \
  --data-binary @artifacts/v1.167/samples/sanity_input.json
