SAMPLE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json

test -f "$SAMPLE" || { echo "SAMPLE NOT FOUND"; exit 1; }

curl -sS --max-time 180 \
  -o /tmp/bplan_result.json \
  -w 'BPLAN HTTP STATUS: %{http_code}\n' \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE"

echo "=== RESPONSE ==="
head -c 1500 /tmp/bplan_result.json 2>/dev/null
echo
