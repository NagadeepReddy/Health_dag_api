status=$(curl -sS -o /tmp/cta_max_smoketest_response.json \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/cta_max_smoketest.json \
  http://127.0.0.1:18080/predict)

echo "HTTP STATUS: $status"

if [ "$status" = "200" ]; then
  head -c 1000 /tmp/cta_max_smoketest_response.json
  echo
else
  podman logs --tail 20 cta-max-serving-poc 2>&1
fi
