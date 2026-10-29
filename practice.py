cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
CANDIDATE=/application1/cta_max_native_release_candidate_20261028
LOG="$BASE/native_concurrent2_weights_fixed.log"

if [ ! -f "$BASE/cta_max/grecbase_integration_weights/att_pooling.rotary_emb.inv_freq.npy" ] || \
   [ ! -f "$BASE/native_concurrent2_static.py" ] || \
   [ ! -f "$BASE/cta_native_benchmark_helper.py" ] || \
   [ ! -f "$CANDIDATE/cta_native_e2e_test.py" ]; then
  echo "STOP: Required files missing"
elif [ -e "$LOG" ]; then
  echo "STOP: Benchmark already attempted"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ]; then
  echo "STOP: Insufficient available RAM"
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
    -v "$BASE:/batchdev:ro" \
    -v "$CANDIDATE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
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
    -e PYTHONPATH=/batchdev:/workspace:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168-max/utils/dependency-utils:/workspace/artifacts/v1.168-max/maxserve_cta_extension \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B /batchdev/native_concurrent2_static.py \
    > "$LOG" 2>&1

  RC=$?
  echo "BENCHMARK EXIT CODE: $RC"
  echo "=== RESULTS ==="
  grep -E 'REQUEST [12]:|HTTP STATUSES|WALL SECONDS|THROUGHPUT RPS|MEAN LATENCY|NATIVE CONCURRENT-2|Error|Traceback|Killed|No exported' "$LOG" | tail -25 || true
  echo "=== FINAL LOG ==="
  tail -12 "$LOG"

  if [ "$RC" -ne 0 ]; then
    echo "STOP: Do not retry automatically"
  fi
fi
