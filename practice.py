cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_after_sibling_fix.log"

if [ ! -f "$BASE/batch2_candidate/cta_max/run_batch2_live_max_inference.py" ]; then
  echo "STOP: Existing batch-2 runner missing"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ]; then
  echo "STOP: Insufficient available memory"
elif [ "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -lt 10485760 ]; then
  echo "STOP: Insufficient /application1 disk space"
else
  timeout --signal=TERM --kill-after=10s 360s \
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never \
    --network=none \
    --memory=16g --memory-swap=16g \
    --pids-limit=32 \
    --tmpfs /tmp:rw,size=1g \
    -v "$PWD:/workspace:ro" \
    -v "$BASE/batch2_candidate:/batchdev:ro" \
    -w /workspace \
    -e HOME=/tmp \
    -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e MODULAR_CACHE_DIR=/tmp/modular \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    -e PYTHONPATH=/batchdev:/workspace \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B -m cta_max.run_batch2_live_max_inference \
    > "$LOG" 2>&1

  RC=$?
  echo "TEST EXIT CODE: $RC"
  echo "=== BATCH-2 RESULTS ==="
  grep -E 'PASS|FAILED|Error|Traceback|CTA BRANCH|OUTPUT SHAPE|DIFFERENCE|Killed|STOP:' \
    "$LOG" | tail -35 || true
  echo "=== FINAL LOG ==="
  tail -12 "$LOG"
fi
