cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -u

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
RUNNER="$DEV/run_distinct_batch2_live_max_inference.py"
SECOND="$DEV/second_real_cta_model_in.pt"
LOG="$DEV/distinct_batch2_execution.log"
NAME=cta-distinct-batch2-final

for f in "$RUNNER" "$SECOND" \
  artifacts/v1.168-max/cta_max/real_sanity_model_in.pt; do
  test -s "$f" || { echo "STOP: Missing $f"; exit 1; }
done

test ! -e "$LOG" || {
  echo "STOP: Existing execution log must be preserved: $LOG"
  exit 1
}

if podman --root /application1/podman/storage \
  --runroot /run/containers/storage container exists "$NAME"; then
  echo "STOP: Named container already exists; inspect it before retrying"
  exit 1
fi

echo "=== DISTINCT REAL CTA BATCH-2 EXECUTION ==="

timeout -k 15s 360s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --name "$NAME" \
  --network none \
  --memory 6g --cpus 2 --pids-limit 128 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e CTA_SECOND_MODEL_INPUT=/batch2/second_real_cta_model_in.pt \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168-max" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /batch2/run_distinct_batch2_live_max_inference.py \
  > "$LOG" 2>&1

RC=$?

echo "=== ACTUAL EXECUTION RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -60 "$LOG"

echo "=== CONTAINER RESULT ==="
timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect "$NAME" \
  --format 'Status={{.State.Status}} Exit={{.State.ExitCode}} OOM={{.State.OOMKilled}}' \
  2>/dev/null || true

echo "=== GPU AVAILABILITY ==="
if command -v nvidia-smi >/dev/null 2>&1; then
  timeout 10s nvidia-smi -L || true
else
  echo "NVIDIA GPU tooling not available on this host"
fi

echo "ORIGINAL DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
echo "LOG PRESERVED: YES"
SH
