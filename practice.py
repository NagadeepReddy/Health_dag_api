timeout 120s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 2g --cpus 2 --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e XDG_CACHE_HOME=/tmp \
  -v /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029:/batch2:ro \
  -w /batch2 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import traceback

print("BATCH-2 REAL GRAPH BUILD: START", flush=True)

try:
    from max.driver import CPU, DeviceRef
    from grecbase_fusion_full_head_72_max_batch2_shapes import (
        build_grecbase_fusion_graph_order_correct_batch2_shapes
    )

    device = DeviceRef.from_device(CPU())
    graph = build_grecbase_fusion_graph_order_correct_batch2_shapes(device)

    print("BATCH-2 GRAPH BUILD: PASS")
    print("GRAPH INPUT COUNT:", len(graph.inputs))

    for i, inp in enumerate(graph.inputs):
        print(f"INPUT {i}: {inp.type.shape}")

except Exception:
    print("BATCH-2 GRAPH BUILD: FAIL")
    traceback.print_exc()
    sys.exit(1)

print("BATCH-2 INFERENCE: NOT YET PERFORMED")
print("FILES MODIFIED: NONE")
print("ORIGINAL DS CODE: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
PY
