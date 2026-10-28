cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_real_execution_retry.log"

echo "=== BATCH-2 RETRY ==="

AVAILABLE_KB=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK_KB=$(df -Pk /application1 | awk 'NR==2 {print $4}')

if [ "$AVAILABLE_KB" -lt 20971520 ]; then
    echo "STOP: Available RAM below 20 GiB"
elif [ "$DISK_KB" -lt 10485760 ]; then
    echo "STOP: Less than 10 GiB free on /application1"
elif [ ! -f "$BASE/batch2_candidate/cta_max/run_batch2_live_max_inference.py" ]; then
    echo "STOP: Batch runner missing"
else
    timeout --signal=TERM --kill-after=10s 360s podman \
      --root /application1/podman/storage \
      --runroot /run/containers/storage \
      run --rm -i \
      --pull=never \
      --network=none \
      --memory=16g \
      --memory-swap=16g \
      --pids-limit=32 \
      --tmpfs /tmp:rw,size=512m \
      -v "$PWD:/workspace:ro" \
      -v "$BASE/batch2_candidate:/batchdev:ro" \
      -w /workspace \
      -e HOME=/tmp \
      -e TMPDIR=/tmp \
      -e XDG_CACHE_HOME=/tmp/cache \
      -e MODULAR_CACHE_DIR=/tmp/modular \
      -e PYTHONDONTWRITEBYTECODE=1 \
      -e MKL_NUM_THREADS=1 \
      -e OPENBLAS_NUM_THREADS=1 \
      -e OMP_NUM_THREADS=1 \
      -e PYTHONPATH=/batchdev:/workspace \
      --entrypoint /opt/venv/bin/python3 \
      localhost/cta-max-faiss:local -B - <<'PY' > "$LOG" 2>&1
from pathlib import Path
import time
import numpy as np
import torch

from cta_max.run_batch2_live_max_inference import infer_max_live

matches = list(
    Path("/workspace/artifacts/v1.168-max").rglob(
        "real_sanity_model_in.pt"
    )
)
assert len(matches) == 1, "STOP: Real input not uniquely found"

model_in = torch.load(
    matches[0], map_location="cpu", weights_only=True
)

start = time.monotonic()
output = infer_max_live(model_in)

if isinstance(output, (tuple, list)) and len(output) == 1:
    output = output[0]

if isinstance(output, torch.Tensor):
    output = output.detach().cpu().numpy()

result = np.asarray(output)

print("BATCH OUTPUT SHAPE:", result.shape, flush=True)
print("ELAPSED SECONDS:", round(time.monotonic()-start, 2), flush=True)

assert result.shape == (2, 2048), "STOP: Incorrect batch output"
assert np.isfinite(result).all(), "STOP: Non-finite output"

diff = float(np.max(np.abs(result[0] - result[1])))
print("DUPLICATE MAX DIFFERENCE:", diff, flush=True)

assert np.allclose(result[0], result[1], rtol=1e-5, atol=1e-5)

print("REAL BATCH-2 EXECUTION: PASS", flush=True)
print("DUPLICATE CONSISTENCY: PASS", flush=True)
PY

    RC=$?
    echo "TEST EXIT CODE: $RC"
    echo "=== RESULTS ==="
    grep -E 'PASS|STOP:|Error|ERROR|Traceback|SHAPE|SECONDS|DIFFERENCE' \
      "$LOG" | tail -20 || true
    echo "LOG: $LOG"
fi
