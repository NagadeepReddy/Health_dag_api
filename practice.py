cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_native_response_trace_1028.log
EXT=artifacts/v1.168-max/maxserve_cta_extension

if [ -e "$LOG" ]; then
  echo "STOP: Trace log already exists"
elif ! grep -q "CTA RESPONSE SOCKET RECEIVED" "$EXT/cta_http_pipeline.py"; then
  echo "STOP: Receiver tracing not installed"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available RAM below 16 GiB"
else
  timeout -s TERM -k 8s 170s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never \
    --network=none --read-only --log-driver=none \
    --memory=8g --memory-swap=8g \
    --cpus=2 --pids-limit=64 \
    --tmpfs /tmp:rw,size=256m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -w /workspace \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
    > "$LOG" 2>&1

  RC=$?
  echo "TEST EXIT CODE: $RC"

  echo "=== RECEIVER AND HTTP RESULTS ==="
  grep -nE \
    'CTA RESPONSE WORKER LOOP|CTA RESPONSE SOCKET RECEIVED|CTA HTTP FANOUT|CTA HTTP QUEUE ITEM|CTA RESPONSE QUEUE SEND|CTA NATIVE HTTP STATUS|CTA RESPONSE:|CTA NATIVE END-TO-END|Traceback|Exception|Error|Killed' \
    "$LOG" | tail -45 || true

  echo "=== LAST 15 LOG LINES ==="
  tail -15 "$LOG"
fi
