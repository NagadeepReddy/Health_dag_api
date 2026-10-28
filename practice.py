cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_native_id_match_1028.log
EXT=artifacts/v1.168-max/maxserve_cta_extension

echo "=== SAFETY CHECK ==="

if ps -p 121339,123853,148527 -o stat= 2>/dev/null | grep -Eq '^[[:space:]]*[RSDTIl]'; then
  echo "STOP: Previous CTA processes still active"

elif [ -e "$LOG" ]; then
  echo "STOP: Diagnostic log already exists"

elif ! grep -q "CTA RESPONSE ID MATCH:" "$EXT/cta_http_pipeline.py"; then
  echo "STOP: Request-ID tracing missing"

elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available RAM below 16 GiB"

else
  echo "SAFETY CHECK: PASS"
  echo "=== RUNNING NATIVE HTTP DIAGNOSTIC ==="

  timeout -s TERM -k 8s 155s podman \
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

  echo "=== HTTP RESPONSE DIAGNOSIS ==="
  grep -nE \
    'CTA RESPONSE ID MATCH|CTA RESPONSE SOCKET RECEIVED|CTA HTTP QUEUE ITEM|CTA RESPONSE QUEUE SEND|CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|Traceback|Exception|Error' \
    "$LOG" | tail -25 || true

  echo "=== FINAL LOG LINES ==="
  tail -10 "$LOG"
fi
