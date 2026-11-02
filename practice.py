ROOT=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage run --rm -i \
  --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/bplan_batch2_graph_dev \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
from max.driver import CPU
from max.graph import DeviceRef
from grecbase_fusion_full_head_72_batch2_v2 import (
    build_grecbase_fusion_graph_order_correct
)

print("BPLAN BATCH-2 GRAPH BUILD: START", flush=True)
graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.from_device(CPU())
)
print("BPLAN BATCH-2 GRAPH BUILD: PASS", flush=True)
print("GRAPH INPUTS:", len(graph.inputs), flush=True)
PY
