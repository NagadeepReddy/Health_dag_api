cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
bash <<'SH'
set -eu

REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
NAME=context_head.deep_embedding_0.weight.npy
MAIN=""

for DIR in \
  "$REPO/artifacts/v1.168-max/cta_max/main_context_weights" \
  /application1/cta_max_true_batch_dev_20261028/cta_max/main_context_weights
do
  if [ -f "$DIR/$NAME" ]; then
    MAIN=$(readlink -f "$DIR")
    break
  fi
done

if [ -z "$MAIN" ]; then
  echo "STOP: Exact trained main-context weight not found"
  echo "=== AVAILABLE MAIN-CONTEXT EXPORTS ==="
  for DIR in \
    "$REPO/artifacts/v1.168-max/cta_max/main_context_weights" \
    /application1/cta_max_true_batch_dev_20261028/cta_max/main_context_weights
  do
    if [ -d "$DIR" ]; then
      echo "DIRECTORY: $DIR"
      find "$DIR" -maxdepth 1 -type f -name '*.npy' | head -25
    fi
  done
  echo "FILES MODIFIED: NONE"
  exit 1
fi

echo "TRAINED MAIN WEIGHTS: FOUND"
echo "SOURCE: $MAIN"

test -f "$DEV/grecbase_fusion_full_head_72_max_batch2_mainfix.py"

LINK="$DEV/main_context_weights"

if [ -L "$LINK" ]; then
  [ "$(readlink "$LINK")" = /weights_main ] || {
    echo "STOP: Existing link differs"
    exit 1
  }
elif [ -e "$LINK" ]; then
  echo "STOP: Existing main-context directory; refusing overwrite"
  exit 1
else
  ln -s /weights_main "$LINK"
fi

echo "MAIN WEIGHT MOUNT: READY"

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
  -v "$MAIN:/weights_main:ro" \
  -v /application1/cta_max_true_batch_dev_20261028/cta_max/sibling_context_weights:/weights_sibling:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import traceback

try:
    from max.driver import CPU
    from max.graph import DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_mainfix import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    print("BATCH-2 GRAPH BUILD: START", flush=True)

    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        DeviceRef.from_device(CPU())
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("INPUT COUNT:", len(graph.inputs))

    for i, item in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", item.type.shape)

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL BATCH-2 INFERENCE: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
SH
