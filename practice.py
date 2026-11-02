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

echo "=== WAITING FOR BPLAN ROUTE ==="
READY=0
for i in $(seq 1 90); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 \
    http://127.0.0.1:18768/bplan/predict)
  if [ "$CODE" = 405 ]; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" -ne 1 ]; then
  echo "BPLAN ROUTE NOT READY"
else
  echo "BPLAN ROUTE READY"
  echo "=== REAL BPLAN POST ==="
  curl -sS --max-time 30 \
    -o /tmp/bplan_result.json \
    -w 'HTTP STATUS: %{http_code}\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @"$SAMPLE"

  echo "=== RESPONSE ==="
  head -c 1200 /tmp/bplan_result.json 2>/dev/null
  echo
fi

echo "=== BPLAN DIAGNOSTICS ==="
"${P[@]}" logs --tail 150 bplan-debug 2>&1 |
  grep -iE 'BPLAN|error|exception|traceback|validation|worker|scheduler|request|response|HTTP/1.1' |
  tail -65
