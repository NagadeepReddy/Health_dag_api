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

data = torch.load(
    root / "bplan_neural_inputs.pt",
    map_location="cpu", weights_only=True
)
data = dict(data)
if "task_in" not in data and "tasks_in" in data:
    data["task_in"] = data["tasks_in"]

labels, arrays = build_real_inputs(model_in=data)
graph = build_grecbase_fusion_graph_order_correct(
    DeviceRef.from_device(CPU())
)

assert len(labels) == len(arrays) == len(graph.inputs) == 72

converted = []
for i, (label, value, inp) in enumerate(zip(labels, arrays, graph.inputs)):
    source = np.asarray(value)
    expected = np.dtype(str(inp.type.dtype).split(".")[-1])

    assert tuple(source.shape) == tuple(int(d) for d in inp.type.shape)

    if source.dtype != expected:
        assert source.dtype == np.dtype("int64")
        assert expected == np.dtype("float32")
        target = source.astype(expected)

        assert np.array_equal(source, target.astype(source.dtype)), (
            f"STOP: lossy conversion at {i}: {label}"
        )

        print(f"CONVERTED {i}: {label} int64 -> float32")
        converted.append(label)

assert len(converted) == 12, (
    f"STOP: expected 12 wide-feature conversions, got {len(converted)}"
)

print("BPLAN INPUT DTYPES: PASS (72/72)")
print("WIDE FEATURES CONVERTED:", len(converted))
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
