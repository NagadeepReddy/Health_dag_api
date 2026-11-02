SAMPLE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json

if ss -ltn | grep -q ':18768 '; then
  echo "BPLAN LISTENER: PASS"
  curl -sS --max-time 120 \
    -o /tmp/bplan_response.json \
    -w 'BPLAN HTTP STATUS: %{http_code}\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @"$SAMPLE"
  if [ -f /tmp/bplan_response.json ]; then
    head -c 1000 /tmp/bplan_response.json
    echo
  fi
else
  echo "BPLAN LISTENER: NOT RUNNING"
fi
