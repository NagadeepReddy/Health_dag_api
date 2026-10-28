cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

CANDIDATE=/application1/cta_max_native_release_candidate_20261028
LOG=/application1/cta_native_release_candidate_validation.log
TEST=artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py

if [ ! -f "$CANDIDATE/cta_router.py" ] ||
   [ ! -f "$CANDIDATE/cta_http_pipeline.py" ] ||
   [ ! -f "$TEST" ]; then
  echo "STOP: Required files missing"

elif [ -e "$LOG" ]; then
  echo "STOP: Validation log already exists"

elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available RAM below 16 GiB"

elif [ "$(df -B1 --output=avail /application1 | tail -1)" -lt 1073741824 ]; then
  echo "STOP: Insufficient disk space"

else
  echo "SAFETY CHECK: PASS"
  echo "TESTING CLEANED RELEASE CANDIDATE"

  timeout -s TERM -k 10s 160s podman \
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
    -v "$CANDIDATE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
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
    -B "/workspace/$TEST" \
    > "$LOG" 2>&1

  RC=$?
  echo "TEST EXIT CODE: $RC"

  echo "=== RELEASE CANDIDATE RESULTS ==="
  grep -E \
    'CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|CTA RESPONSE QUEUE SEND|CTA HTTP QUEUE ITEM|Traceback|Exception|Error' \
    "$LOG" | tail -15 || true

  if [ "$RC" -eq 0 ] &&
     grep -q 'CTA NATIVE HTTP STATUS: 200' "$LOG" &&
     grep -q 'CTA NATIVE END-TO-END: PASS' "$LOG"; then
    echo "RELEASE CANDIDATE RUNTIME: PASS"
  else
    echo "RELEASE CANDIDATE RUNTIME: NOT PASSED"
    echo "DO NOT RETRY OR MODIFY WORKING VERSION"
    tail -12 "$LOG"
  fi
fi
