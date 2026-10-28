cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_after_weight_fix.log"

echo "=== REAL BATCH-2 TEST ==="

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

if [ "$RAM" -lt 20971520 ]; then
  echo "STOP: Less than 20 GiB available RAM"
elif [ "$DISK" -lt 10485760 ]; then
  echo "STOP: Less than 10 GiB available disk"
elif [ ! -f "$BASE/batch2_candidate/cta_max/run_batch2_live_max_inference.py" ]; then
  echo "STOP: Batch runner missing"
else
  timeout --signal=TERM --kill-after=10s 360s \
  podman \
    --root /application1/podman/storage \
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
import numpy as np
import torch
import time
from cta_max.run_batch2_live_max_inference import infer_max_live

paths = list(Path("artifacts/v1.168-max").rglob("real_sanity_model_in.pt"))
assert len(paths) == 1, "STOP: Real input not uniquely located"

data = torch.load(paths[0], map_location="cpu", weights_only=True)

start = time.monotonic()
output = infer_max_live(data)
elapsed = time.monotonic() - start

if isinstance(output, (tuple, list)) and len(output) == 1:
    output = output[0]
if isinstance(output, torch.Tensor):
    output = output.detach().cpu().numpy()

result = np.asarray(output)
print("OUTPUT SHAPE:", result.shape, flush=True)
print("ELAPSED SECONDS:", round(elapsed, 2), flush=True)

assert result.shape == (2, 2048), "STOP: Incorrect batch output"
assert np.isfinite(result).all(), "STOP: Non-finite output"

diff = float(np.max(np.abs(result[0] - result[1])))
print("DUPLICATE MAX DIFFERENCE:", diff, flush=True)
assert np.allclose(result[0], result[1], rtol=1e-5, atol=1e-5)

print("REAL BATCH-2 INFERENCE: PASS", flush=True)
print("DUPLICATE CONSISTENCY: PASS", flush=True)
PY

  RC=$?
  echo "TEST EXIT CODE: $RC"
  echo "=== RESULTS ==="
  grep -E 'PASS|STOP:|Error|ERROR|Traceback|SHAPE|SECONDS|DIFFERENCE|Killed' "$LOG" | tail -20 || true
  echo "LOG: $LOG"
fi
