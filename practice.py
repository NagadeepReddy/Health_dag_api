ROOT=/application1/sajjna8/rt-pzai-bplan-v1
SAMPLE="$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -f "$SAMPLE" || { echo "STOP: sample missing"; exit 1; }

"${P[@]}" rm -f bplan-debug 2>/dev/null || true

"${P[@]}" run -d --name bplan-debug --pull=never \
  --network=host \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher

echo "=== WAITING FOR SERVER ==="
READY=0
for i in $(seq 1 60); do
  if curl -fsS --max-time 2 http://127.0.0.1:18768/openapi.json >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [ "$READY" -eq 1 ]; then
  echo "=== SINGLE BPLAN REQUEST ==="
  curl -sS --max-time 20 \
    -o /tmp/bplan_debug_response.json \
    -w 'HTTP STATUS: %{http_code}\n' \
    -X POST http://127.0.0.1:18768/bplan/predict \
    -H 'Content-Type: application/json' \
    --data-binary @"$SAMPLE" || true
else
  echo "SERVER DID NOT BECOME READY"
fi

echo "=== BPLAN WORKER DIAGNOSTICS ==="
"${P[@]}" logs --tail 250 bplan-debug 2>&1 | \
  grep -iE -C 3 'BPLAN|factory|scheduler|worker|queue|response|error|traceback|exception|failed|type' | \
  tail -140

echo "=== CONTAINER STATUS ==="
"${P[@]}" ps -a --filter name=bplan-debug
