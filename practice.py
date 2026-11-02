ROOT=/application1/sajjna8/rt-pzai-bplan-v1
SAMPLE="$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -f "$SAMPLE" || { echo "STOP: Sample missing"; exit 1; }

"${P[@]}" rm -f bplan-debug 2>/dev/null || true

"${P[@]}" run -d --name bplan-debug --pull=never \
  --network=host \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher || exit 1

echo "=== WAIT FOR ROUTE ==="
READY=0
for i in $(seq 1 120); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 \
    http://127.0.0.1:18768/bplan/predict)
  if [ "$CODE" = 405 ]; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" = 1 ]; then
  echo "BPLAN ROUTE: READY"
  echo "=== REAL BPLAN POST ==="
  curl -sS --max-time 180 \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @"$SAMPLE" \
    -o /tmp/bplan_verified_result.json \
    -w 'HTTP STATUS: %{http_code}\nTIME: %{time_total}s\n'

  echo "=== RESPONSE ==="
  head -c 800 /tmp/bplan_verified_result.json 2>/dev/null
  echo
else
  echo "BPLAN ROUTE: NOT READY"
fi

echo "=== REAL MAX EXECUTION LOGS ==="
"${P[@]}" logs --tail 300 bplan-debug 2>&1 |
  grep -iE 'BPLAN REAL MAX|BPLAN|predict_raw|exception|traceback|error in|worker failed|HTTP/1.1' |
  tail -65
