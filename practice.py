ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== REAL BPLAN HTTP REQUEST ==="
curl -sS --max-time 30 \
  -o /tmp/bplan_http_result.json \
  -w 'HTTP STATUS: %{http_code}\nTIME: %{time_total}s\n' \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"

echo "=== RESPONSE ==="
head -c 1200 /tmp/bplan_http_result.json 2>/dev/null
echo

echo "=== ACTUAL BPLAN CONTAINER LOGS ==="
"${P[@]}" logs --tail 120 bplan-debug 2>&1 | tail -100
