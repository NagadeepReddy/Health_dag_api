status=$(curl -sS \
  -o /tmp/cta_max_tiles_response.json \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/cta_max_tiles_test.json \
  http://127.0.0.1:18080/predict)

echo "HTTP STATUS: $status"
echo "MAX EXECUTION:"
podman logs --tail 35 cta-max-serving-poc 2>&1 | grep -E 'MAX INFERENCE EXECUTED:|KeyError:|RuntimeError:|ValueError:|AssertionError:|Traceback' || true
