cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
RUNNER="$BASE/native_concurrent2_realfile.py"
CANDIDATE=/application1/cta_max_native_release_candidate_20261028
LOG="$BASE/native_concurrent2_cachefix.log"

if [ ! -f "$RUNNER" ] || [ ! -f "$CANDIDATE/cta_native_e2e_test.py" ]; then
  echo "STOP: Required files missing"
elif [ -e "$LOG" ]; then
  echo "STOP: Log already exists"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ]; then
  echo "STOP: Available RAM below 20 GiB"
elif [ "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -lt 10485760 ]; then
  echo "STOP: Insufficient disk space"
else
  timeout --signal=TERM --kill-after=10s 420s \
  podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never \
    --network=none --read-only --log-driver=none \
    --memory=12g --memory-swap=12g \
    --cpus=2 --pids-limit=256 \
    --tmpfs /tmp:rw,size=1g,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=512m,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -v "$CANDIDATE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -v "$RUNNER:/batchdev/native_concurrent2_realfile.py:ro" \
    -w /workspace \
    -e HOME=/tmp \
    -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e MODULAR_CACHE_DIR=/tmp/modular \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B /batchdev/native_concurrent2_realfile.py \
    > "$LOG" 2>&1

  RC=$?
  echo "BENCHMARK EXIT CODE: $RC"
  echo "=== PERFORMANCE RESULTS ==="
  grep -E 'REQUEST [12]:|HTTP STATUSES|WALL SECONDS|THROUGHPUT RPS|MEAN LATENCY|NATIVE CONCURRENT-2|Error|Traceback|Killed|STOP' "$LOG" | tail -25 || true
  echo "=== LAST LOG LINES ==="
  tail -12 "$LOG"

  if [ "$RC" -ne 0 ]; then
    echo "BENCHMARK NOT PASSED - DO NOT RETRY AUTOMATICALLY"
  fi
fi
