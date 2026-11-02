SAMPLE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -f "$SAMPLE" || { echo "STOP: sample missing"; exit 1; }

echo "=== REAL BPLAN POST ==="
curl -sS --max-time 20 \
  -o /tmp/bplan_post_result.json \
  -w 'HTTP STATUS: %{http_code}\n' \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE"

echo "=== RESPONSE ==="
head -c 1000 /tmp/bplan_post_result.json 2>/dev/null
echo

echo "=== WORKER LOGS ==="
"${P[@]}" logs --tail 200 bplan-debug 2>&1 | \
  grep -iE 'BPLAN|factory|worker|scheduler|queue|response|error|traceback|exception|failed|type' | tail -65
