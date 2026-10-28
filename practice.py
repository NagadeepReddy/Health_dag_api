cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_native_id_match_1028.log
EXT=artifacts/v1.168-max/maxserve_cta_extension

echo "=== CHECK REMAINING CTA PROCESSES ==="

ps -p 121339,121386,121387,121394,123853,123905,123913,148527,148578,148579,148589 \
  -o pid,ppid,stat,rss,comm 2>/dev/null || true

echo "=== SAFETY CHECK ==="

if [ -e "$LOG" ]; then
  echo "STOP: Diagnostic log already exists"
elif ! grep -q "CTA RESPONSE ID MATCH:" "$EXT/cta_http_pipeline.py"; then
  echo "STOP: ID tracing missing"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available memory below 16 GiB"
elif ps -p 121339,121386,121387,121394,123853,123905,123913,148527,148578,148579,148589 \
  -o stat= 2>/dev/null | grep -Eq '^[^Z[:space:]]'; then
  echo "STOP: Previous CTA processes still active"
else
  echo "SAFETY CHECK: PASS"

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

  echo "TEST EXIT CODE: $?"
  echo "=== IMPORTANT RESULTS ==="

  grep -nE \
    'CTA RESPONSE ID MATCH|CTA RESPONSE SOCKET RECEIVED|CTA HTTP QUEUE ITEM|CTA RESPONSE QUEUE SEND|CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|Traceback|Exception' \
    "$LOG" | tail -25 || true

  echo "=== LAST LOGS ==="
  tail -10 "$LOG"
fi
