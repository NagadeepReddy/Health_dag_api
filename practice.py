ROOT=/application1/sajjna8/rt-pzai-bplan-v1
SAMPLE=""

for v in v1.113 v1.110 v1.109; do
  SAMPLE=$(find "$ROOT/artifacts/$v" -type f -name 'test_sample*.json' 2>/dev/null | sort | head -n 1)
  [ -n "$SAMPLE" ] && break
done

if [ -z "$SAMPLE" ]; then
  echo "STOP: No BPLAN test JSON found"
else
  echo "BPLAN SAMPLE: $SAMPLE"

  curl -sS --max-time 30 \
    -o /tmp/bplan_next_response.json \
    -w 'BPLAN HTTP STATUS: %{http_code}\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @"$SAMPLE"

  if [ -f /tmp/bplan_next_response.json ]; then
    head -c 1000 /tmp/bplan_next_response.json
    echo
  fi
fi
