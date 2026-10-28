cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_native_queue_identity_1028.log
EXT=artifacts/v1.168-max/maxserve_cta_extension

if [ -e "$LOG" ]; then
  echo "STOP: Log already exists"
elif ! grep -q "CTA ROUTE QUEUE ID:" "$EXT/cta_router.py"; then
  echo "STOP: Route diagnostic missing"
elif ! grep -q "CTA RECEIVER ENGINE ID:" "$EXT/cta_http_pipeline.py"; then
  echo "STOP: Receiver diagnostic missing"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available memory below 16 GiB"
else
  echo "SAFETY CHECK: PASS"

  timeout -s TERM -k 8s 170s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never --init \
    --network=none --read-only --log-driver=none \
    --memory=8g --memory-swap=8g \
    --cpus=2 --pids-limit=64 \
    --tmpfs /tmp:rw,size=256m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -w /workspace \
    -e HOME=/tmp \
    -e XDG_CACHE_HOME=/tmp \
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

  echo "=== QUEUE IDENTITY AND HTTP RESULT ==="
  grep -nE \
    'CTA ROUTE QUEUE ID|CTA RECEIVER ENGINE ID|CTA RESPONSE ID MATCH|CTA RESPONSE SOCKET RECEIVED|CTA HTTP QUEUE ITEM|CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|CTA RESPONSE WORKER LOOP|Traceback|Exception|Timeout' \
    "$LOG" | tail -35 || true

  echo "=== LAST 12 LOG LINES ==="
  tail -12 "$LOG"
fi
