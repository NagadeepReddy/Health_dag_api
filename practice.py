set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
WEIGHTS="$PWD/artifacts/v1.168-max/cta_max/grecbase_integration_weights"
LINK="$DEV/grecbase_integration_weights"

test -f "$WEIGHTS/seq_dense.weight.npy" || {
  echo "STOP: Original trained MAX weight file not found"
  exit 1
}

test -f "$DEV/grecbase_fusion_full_head_72_max_batch2_blockfix.py" || {
  echo "STOP: Batch-2 graph file missing"
  exit 1
}

if [ -L "$LINK" ]; then
  test "$(readlink "$LINK")" = \
    "/workspace/artifacts/v1.168-max/cta_max/grecbase_integration_weights" || {
    echo "STOP: Existing weight link differs"
    exit 1
  }
elif [ -e "$LINK" ]; then
  echo "STOP: Weight destination already exists"
  exit 1
else
  ln -s \
    /workspace/artifacts/v1.168-max/cta_max/grecbase_integration_weights \
    "$LINK"
fi

echo "ORIGINAL WEIGHTS: LINKED READ-ONLY"

timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

print("BATCH-2 GRAPH BUILD: START", flush=True)

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_blockfix import (
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

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
PY
