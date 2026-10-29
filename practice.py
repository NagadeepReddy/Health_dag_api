test -f artifacts/v1.168-max/cta_max/run_live_max_inference.py && \
test -f /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/grecbase_fusion_full_head_72_max_batch2_shapes.py && \
timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -v "$PWD:/workspace:ro" \
  -v /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029:/batch2:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
import sys
import traceback

sys.path.insert(0, "/batch2")

print("BATCH-2 REAL GRAPH BUILD: START", flush=True)

try:
    from max.driver import CPU, DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_shapes import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    device = DeviceRef.from_device(CPU())
    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(device)

    print("BATCH-2 GRAPH BUILD: PASS")
    print("GRAPH INPUTS:", len(graph.inputs))

    for i, inp in enumerate(graph.inputs):
        print("INPUT", i, "SHAPE:", inp.type.shape)

except Exception:
    print("BATCH-2 GRAPH BUILD: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL INFERENCE: NOT YET PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
PY
