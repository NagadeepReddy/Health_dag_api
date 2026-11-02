ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${P[@]}" run --rm --pull=never --network=none \
  --memory=16g \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import sys, types, importlib
from pathlib import Path
from max.driver import CPU
from max.graph import DeviceRef

root = Path("/workspace/artifacts/v1.113-max/bplan_batch2_graph_dev")
target = root / "grecbase_fusion_full_head_72_batch2_v2.py"

assert target.is_file(), f"Missing candidate: {target}"

pkg = types.ModuleType("cta_max")
pkg.__path__ = [str(root)]
sys.modules["cta_max"] = pkg
sys.path.insert(0, str(root))

print("BPLAN BATCH-2 MAX GRAPH BUILD: START", flush=True)

module = importlib.import_module(
    "cta_max.grecbase_fusion_full_head_72_batch2_v2"
)

graph = module.build_grecbase_fusion_graph_order_correct(
    DeviceRef.from_device(CPU())
)

print("GRAPH BUILD: PASS")
print("TOTAL INPUTS:", len(graph.inputs))

for i, item in enumerate(graph.inputs):
    print("INPUT", i, "SHAPE", item.type.shape)

print("BPLAN BATCH-2 GRAPH BUILD: PASS")
print("GRAPH COMPILATION WITH BPLAN WEIGHTS: PENDING")
print("ORIGINAL SOURCES: UNCHANGED")
PY
