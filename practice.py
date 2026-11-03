ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

if [ "$(id -u)" -ne 0 ]; then
  echo "STOP: Use the authorized ROOT shell, not sajjna8."
else
  echo "=== RECREATE ONLY BPLAN DEBUG CONTAINER ==="
  "${P[@]}" rm -f --ignore bplan-debug

  if "${P[@]}" run -d \
    --name bplan-debug \
    --pull=never \
    --network=host \
    -v "$ROOT:/workspace:ro" \
    -w /workspace \
    -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -m bplan_native_serve_dev.bplan_native_launcher
  then
    READY=0

    for i in $(seq 1 90); do
      CODE=$(curl -s --max-time 2 -o /dev/null \
        -w '%{http_code}' http://127.0.0.1:18768/bplan/predict)
      if [ "$CODE" = "405" ]; then
        READY=1
        break
      fi
      sleep 2
    done

    if [ "$READY" = 1 ]; then
      echo "=== REAL BPLAN HTTP REQUEST ==="
      curl -sS --max-time 150 \
        -o /tmp/bplan_response_trace.json \
        -w 'HTTP STATUS: %{http_code}; TIME: %{time_total}s\n' \
        -X POST http://127.0.0.1:18768/bplan/predict \
        -H 'Content-Type: application/json' \
        --data-binary @"$ROOT/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json"

      echo "=== HTTP RESPONSE ==="
      head -c 500 /tmp/bplan_response_trace.json 2>/dev/null
      echo
    else
      echo "BPLAN ROUTE NOT READY"
    fi
  else
    echo "BPLAN CONTAINER CREATION FAILED"
  fi

  echo "=== BPLAN RESPONSE DELIVERY ==="
  "${P[@]}" logs --tail 250 bplan-debug 2>&1 |
    grep -E 'BPLAN TRACE|BPLAN REAL MAX|BPLAN RESPONSE SEND|Traceback|Error|ERROR' |
    tail -45
fi
