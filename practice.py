curl --noproxy '*' --fail -sS \
  --max-time 300 \
  -o /dev/null \
  -w 'HTTP STATUS: %{http_code}\nWARM CTA LATENCY: %{time_total} seconds\n' \
  -H "Content-Type: application/json" \
  --data-binary @/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json \
  http://127.0.0.1:8765/v2/cta/predict
