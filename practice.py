ROOT=/application1/sajjna8/rt-pzai-bplan-v1
SAMPLE="$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== REAL BPLAN POST ==="
curl -sS --max-time 45 \
  -X POST http://127.0.0.1:18768/bplan/predict \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  -o /tmp/bplan_result.json \
  -w 'HTTP STATUS: %{http_code}\nTIME: %{time_total}s\n'

echo "=== RESPONSE ==="
head -c 1200 /tmp/bplan_result.json 2>/dev/null
echo

echo "=== BPLAN WORKER DIAGNOSTICS ==="
"${P[@]}" logs --tail 250 bplan-debug 2>&1 |
  grep -iE 'BPLAN|validationerror|missing required|worker failed|scheduling|request_id|response|traceback|error in|HTTP/1.1|modelworker' |
  tail -75
