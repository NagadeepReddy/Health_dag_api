set -eu

REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029

WEIGHTS=""

for CANDIDATE in \
  "$REPO/artifacts/v1.168-max/cta_max/sibling_context_weights" \
  /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights
do
  if [ -d "$CANDIDATE" ] && \
     find -L "$CANDIDATE" -maxdepth 1 -type f -name '*.npy' | grep -q .; then
    WEIGHTS=$(readlink -f "$CANDIDATE")
    break
  fi
done

if [ -z "$WEIGHTS" ]; then
  echo "STOP: Previously exported sibling weights not accessible"
  exit 1
fi

test -f "$DEV/grecbase_fusion_full_head_72_max_batch2_siblingfix.py"

python3 -S -B - "$WEIGHTS" <<'PY'
from pathlib import Path
import sys

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
weights = Path(sys.argv[1])
files = sorted(weights.glob("*.npy"))
assert len(files) >= 10, f"STOP: Only {len(files)} weight files"

link = dev / "sibling_context_weights"
target = Path("/weights_sibling")

if link.is_symlink():
    assert link.readlink() == target, "STOP: Existing link differs"
elif link.exists():
    raise SystemExit("STOP: Destination exists; refusing overwrite")
else:
    link.symlink_to(target, target_is_directory=True)

print("EXISTING SIBLING WEIGHTS:", len(files))
print("SOURCE:", weights)
print("WEIGHT LINK: PASS")
print("ORIGINAL WEIGHTS: UNCHANGED")
PY

echo "=== REAL BATCH-2 GRAPH CONSTRUCTION ==="

timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max \
  -v "$REPO:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$WEIGHTS:/weights_sibling:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_siblingfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))

    for i, item in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", item.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 EXECUTION: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
