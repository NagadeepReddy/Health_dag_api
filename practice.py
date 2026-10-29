test -f artifacts/v1.168-max/cta_max/att_pooling_max.py && \
test -f /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/grecbase_fusion_full_head_72_max_batch2_shapes.py && \
timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max \
  -v "$PWD:/workspace:ro" \
  -v /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029:/batch2:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import traceback
import sys

print("REAL BATCH-2 GRAPH BUILD: START", flush=True)

try:
    from max.driver import CPU
    from max.graph import DeviceRef

    from cta_max.att_pooling_max import AttPoolingBlockMAX
    print("ORIGINAL CTA PACKAGE IMPORT: PASS", flush=True)

    from grecbase_fusion_full_head_72_max_batch2_shapes import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )
    print("BATCH-2 GRAPH IMPORT: PASS", flush=True)

    device_ref = DeviceRef.from_device(CPU())

    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(
        device_ref
    )

    print("BATCH-2 GRAPH CONSTRUCTION: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))

    for i, item in enumerate(graph.inputs):
        print(f"INPUT {i}: {item.type.shape}")

except Exception:
    print("BATCH-2 GRAPH CONSTRUCTION: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("REAL INFERENCE: NOT YET PERFORMED")
print("DS CODE: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("MAX SERVE STARTUP: NOT PERFORMED")
PY
