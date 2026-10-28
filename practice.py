cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_branch_diagnostic.log"

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

if [ "$RAM" -lt 20971520 ] || [ "$DISK" -lt 10485760 ]; then
  echo "STOP: Insufficient available RAM or disk"
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
    localhost/cta-max-faiss:local -B - <<'PY' > "$LOG" 2>&1
from pathlib import Path
import torch
from cta_max.run_batch2_live_max_inference import infer_max_live

paths = list(Path("artifacts/v1.168-max").rglob("real_sanity_model_in.pt"))
assert len(paths) == 1, "STOP: Real input ambiguous"

data = torch.load(paths[0], map_location="cpu", weights_only=True)
result = infer_max_live(data)
print("BATCH TEST RETURNED:", type(result).__name__, flush=True)
PY

  RC=$?
  echo "TEST EXIT CODE: $RC"
  echo "=== BRANCH DIAGNOSTICS ==="
  grep -E 'CTA BRANCH |Failed to create op|#moshape|Traceback|ValueError|Error|PASS|BATCH TEST RETURNED' \
    "$LOG" | tail -30 || true
  echo "LOG: $LOG"
fi
