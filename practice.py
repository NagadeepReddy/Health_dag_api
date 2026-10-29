cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -u

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
BACKEND="$DEV/real_max_batch2_backend.py"
LOG="$DEV/real_max_batch2_validation.log"

test -s "$BACKEND" || { echo "STOP: Backend missing"; exit 1; }
test -d "$CAND" || { echo "STOP: Batch-2 candidate missing"; exit 1; }
test -s artifacts/v1.168-max/cta_max/real_sanity_model_in.pt || {
  echo "STOP: Real model input missing"; exit 1;
}
test ! -e "$LOG" || { echo "STOP: Preserve existing log"; exit 1; }

# Correct an undefined device reference only if needed.
python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")
s = p.read_text()

if (
    "build_grecbase_fusion_graph_order_correct(device_ref)" in s
    and "device_ref = DeviceRef.from_device(device)" not in s
):
    anchor = "    device = CPU()\n"
    assert s.count(anchor) == 1, "STOP: Device setup differs"
    assert "from max.graph import DeviceRef" in s, "STOP: DeviceRef import missing"

    updated = s.replace(
        anchor,
        anchor + "    device_ref = DeviceRef.from_device(device)\n"
    )
    ast.parse(updated)

    backup = p.with_suffix(".py.before_device_fix.bak")
    assert not backup.exists(), "STOP: Existing backup"
    backup.write_bytes(p.read_bytes())
    p.write_text(updated)
    print("DEV DEVICE REFERENCE: CORRECTED")
else:
    print("DEV DEVICE REFERENCE: NO CHANGE")

ast.parse(p.read_text())
print("BACKEND PYTHON SYNTAX: PASS")
PY

RC=$?
if [ "$RC" -ne 0 ]; then exit "$RC"; fi

echo "=== EXECUTING TWO REAL CTA MODEL INPUTS THROUGH MAX ==="

timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH="/batch2:/workspace/artifacts/v1.168-max:$CAND" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import numpy as np
import torch
from real_max_batch2_backend import infer_max_batch

source = "/workspace/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"

print("REAL CTA BATCH-2: START", flush=True)

first = torch.load(source, map_location="cpu", weights_only=True)
second = torch.load(source, map_location="cpu", weights_only=True)

assert isinstance(first, dict)
assert isinstance(second, dict)

result = np.asarray(
    infer_max_batch(first, second),
    dtype=np.float32
)

print("MAX OUTPUT SHAPE:", result.shape, flush=True)

assert result.shape == (2, 2048), "Unexpected MAX batch output"
assert np.isfinite(result).all(), "Non-finite MAX output"

print("BATCH OUTPUT SHAPE: PASS", flush=True)
print("BOTH OUTPUTS FINITE: PASS", flush=True)
print(
    "DUPLICATE INPUT OUTPUT PARITY:",
    "PASS" if np.allclose(result[0], result[1], atol=1e-5) else "FAIL",
    flush=True
)

assert np.allclose(result[0], result[1], atol=1e-5)

print("REAL MAX BATCH-2 EXECUTION: PASS", flush=True)
PY

RC=$?

echo "=== REAL MAX BATCH-2 RESULTS ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -70 "$LOG"

if [ "$RC" -ne 0 ]; then
  echo "REAL MAX BACKEND: NOT VALIDATED"
  exit "$RC"
fi

grep -q 'REAL MAX BATCH-2 EXECUTION: PASS' "$LOG" || {
  echo "STOP: Success marker missing"
  exit 1
}

echo "REAL MAX BATCH-2: VALIDATED"
echo "DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
