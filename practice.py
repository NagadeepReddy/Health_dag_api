cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
LOG="$BASE/batch2_pids256_test.log"

if [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ] || \
   [ "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -lt 10485760 ]; then
  echo "STOP: Insufficient available RAM or disk"
else
  timeout --signal=TERM --kill-after=10s 360s \
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never \
    --network=none \
    --memory=16g --memory-swap=16g \
    --pids-limit=256 \
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
from cta_max.run_batch2_live_max_inference import infer_max_live

paths = list(Path("artifacts/v1.168-max").rglob("real_sanity_model_in.pt"))
assert len(paths) == 1, "STOP: Real inputs ambiguous"

data = torch.load(paths[0], map_location="cpu", weights_only=True)

print("BATCH-2 START", flush=True)
output = infer_max_live(data)

if isinstance(output, (list, tuple)) and len(output) == 1:
    output = output[0]
if isinstance(output, torch.Tensor):
    output = output.detach().cpu().numpy()

result = np.asarray(output)
print("OUTPUT SHAPE:", result.shape, flush=True)
assert result.shape == (2, 2048)
assert np.isfinite(result).all()

diff = float(np.max(np.abs(result[0] - result[1])))
print("DUPLICATE DIFFERENCE:", diff, flush=True)
assert np.allclose(result[0], result[1], rtol=1e-5, atol=1e-5)

print("BATCH-2 INFERENCE: PASS", flush=True)
PY

  RC=$?
  echo "TEST EXIT CODE: $RC"
  echo "=== RESULTS ==="
  grep -E 'PASS|SHAPE|DIFFERENCE|pthread|Error|Traceback|Killed|Failed' \
    "$LOG" | tail -25 || true
  echo "=== LAST LOG LINES ==="
  tail -8 "$LOG"
fi
