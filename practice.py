cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

REPO="$PWD"
BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_real_execution.log"

echo "=== BATCH-2 FINAL TEST ==="

if [ ! -f "$BASE/batch2_candidate/cta_max/run_batch2_live_max_inference.py" ]; then
    echo "STOP: Batch-2 runner missing"
elif [ ! -f "$BASE/batch2_candidate/cta_max/run_batch2_contract.py" ]; then
    echo "STOP: Batch-2 contract missing"
elif [ "$(awk '/MemAvailable:/ {print int($2/1024/1024)}' /proc/meminfo)" -lt 20 ]; then
    echo "STOP: Less than 20 GiB available; no model started"
elif ! podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    image exists localhost/cta-max-faiss:local; then
    echo "STOP: Local development image unavailable"
else
    timeout 360s podman \
      --root /application1/podman/storage \
      --runroot /run/containers/storage \
      run --rm -i \
      --pull=never \
      --network=none \
      --memory=16g \
      --memory-swap=16g \
      --pids-limit=32 \
      --read-only \
      --tmpfs /tmp:rw,size=512m \
      -v "$REPO:/workspace:ro" \
      -v "$BASE/batch2_candidate:/batchdev:ro" \
      -w /workspace \
      -e HOME=/tmp \
      -e TMPDIR=/tmp \
      -e XDG_CACHE_HOME=/tmp/cache \
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

assert len(matches) == 1, (
    f"STOP: Expected one saved real input, found {len(matches)}"
)

model_in = torch.load(
    matches[0], map_location="cpu", weights_only=True
)

print("REAL CTA INPUT: LOADED", flush=True)

start = time.monotonic()
output = infer_max_live(model_in)
elapsed = time.monotonic() - start

if isinstance(output, (tuple, list)) and len(output) == 1:
    output = output[0]

if isinstance(output, torch.Tensor):
    output = output.detach().cpu().numpy()

result = np.asarray(output)

print("BATCH-2 OUTPUT SHAPE:", result.shape, flush=True)
print("BATCH-2 ELAPSED SECONDS:", round(elapsed, 2), flush=True)

assert result.shape == (2, 2048), \
    f"STOP: Incorrect batch output shape {result.shape}"

assert np.isfinite(result).all(), \
    "STOP: Non-finite model output"

diff = np.max(np.abs(result[0] - result[1]))
print("DUPLICATE REQUEST MAX DIFFERENCE:", float(diff), flush=True)

assert np.allclose(
    result[0], result[1], rtol=1e-5, atol=1e-5
), "STOP: Duplicate requests produced inconsistent results"

print("REAL BATCH-2 EXECUTION: PASS", flush=True)
print("BATCH OUTPUT FINITE: PASS", flush=True)
print("DUPLICATE CONSISTENCY: PASS", flush=True)
print("DS CODE: UNCHANGED", flush=True)
PY

    RC=$?
    echo "=== BATCH-2 EXECUTION RESULTS ==="
    grep -E 'PASS|STOP:|ERROR|Error|Traceback|OUTPUT SHAPE|ELAPSED|DIFFERENCE' \
      "$LOG" | tail -20 || true
    echo "TEST EXIT CODE: $RC"
    echo "LOG: $LOG"
fi
