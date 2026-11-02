SAMPLE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json

curl -sS --max-time 30 \
  -o /tmp/bplan_next_response.json \
  -w '\nBPLAN HTTP STATUS: %{http_code}\n' \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE"

echo "=== RESPONSE ==="
head -c 1000 /tmp/bplan_next_response.json
echo
