REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys, types, torch, numpy as np
from pathlib import Path
from max.driver import CPU
from max.graph import DeviceRef

root = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
dev = root / "bplan_max_dev"

pkg = types.ModuleType("cta_max")
pkg.__path__ = [str(dev)]
sys.modules["cta_max"] = pkg
sys.path.insert(0, str(dev))

from run_real_sanity_input_adapter import build_real_inputs
from grecbase_fusion_full_head_72_max import build_grecbase_fusion_graph_order_correct

data = torch.load(root / "bplan_neural_inputs.pt",
                  map_location="cpu", weights_only=True)
data = dict(data)
if "task_in" not in data and "tasks_in" in data:
    data["task_in"] = data["tasks_in"]

labels, arrays = build_real_inputs(model_in=data)
graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.from_device(CPU())
)

assert len(arrays) == len(graph.inputs) == 72

mismatches = []
for i, (label, arr, inp) in enumerate(zip(labels, arrays, graph.inputs)):
    actual = np.asarray(arr)
    expected_dtype = str(inp.type.dtype).lower()
    if actual.dtype.name != expected_dtype:
        exact = None
        if actual.dtype == np.int64 and expected_dtype == "float32":
            exact = bool(np.array_equal(
                actual, actual.astype(np.float32).astype(np.int64)
            ))
        mismatches.append((i, label, actual.dtype.name,
                           expected_dtype, exact))

for item in mismatches:
    print("DTYPE MISMATCH:", item)

print("TOTAL DTYPE MISMATCHES:", len(mismatches))
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
