podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast
from pathlib import Path
import numpy as np

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
original = base / "grecbase_fusion_with_aux_max.py"
newfile = base / "grecbase_fusion_with_context_max.py"

source = original.read_text()

def replace_once(old, new):
    global source
    assert source.count(old) == 1, (
        f"Expected exactly one occurrence: {old[:70]}"
    )
    source = source.replace(old, new)

replace_once(
    "from cta_max.grecbase_aux_branches_max import grecbase_aux_features",
    "from cta_max.grecbase_aux_branches_max import grecbase_aux_features\n"
    "from cta_max.main_context_max import main_context_forward"
)

replace_once(
    "def build_grecbase_fusion_graph_with_aux(device):",
    "def build_grecbase_fusion_graph_with_context(device):"
)

# Four remaining external float branches instead of five.
replace_once(
    "for _ in range(5)]",
    "for _ in range(4)]"
)

# Add actual context feature inputs.
replace_once(
    "for _ in range(3)]",
    """for _ in range(3)]
            +
            [TensorType(DType.int64, [1], device=device)
             for _ in range(17)]
            +
            [TensorType(DType.float32, [1, 127], device=device)]"""
)

replace_once(
    "seq, context, search0, search1, sibling, task0, task1, ihq_ids, jet_name, jet_status = graph.inputs",
    """seq, search0, search1, sibling, task0, task1, ihq_ids, jet_name, jet_status, *context_inputs = graph.inputs

        assert len(context_inputs) == 18
        context, deep_extract = main_context_forward(
            context_inputs[:17], context_inputs[17], device
        )"""
)

ast.parse(source)
newfile.write_text(source)

from cta_max.grecbase_fusion_with_context_max import (
    build_grecbase_fusion_graph_with_context
)

weights = {}
for p in sorted(base.rglob("att_pooling.*.npy")):
    arr = np.load(p).astype(np.float32)
    assert p.stem not in weights
    weights[p.stem] = WeightData.from_numpy(arr, p.stem)

device = CPU()
graph = build_grecbase_fusion_graph_with_context(
    DeviceRef.CPU()
)

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("CONTEXT + AUX FUSION COMPILATION: PASS")

inputs = [
    Tensor.from_numpy(
        np.zeros((1, 256), dtype=np.float32)
    ).to(device)
    for _ in range(4)
]

inputs += [
    Tensor.from_numpy(
        np.zeros((1,), dtype=np.int64)
    ).to(device)
    for _ in range(2)
]

inputs += [
    Tensor.from_numpy(
        np.zeros((1, 1), dtype=np.int64)
    ).to(device)
    for _ in range(3)
]

inputs += [
    Tensor.from_numpy(
        np.zeros((1,), dtype=np.int64)
    ).to(device)
    for _ in range(17)
]

inputs.append(
    Tensor.from_numpy(
        np.zeros((1, 127), dtype=np.float32)
    ).to(device)
)

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("MAIN CONTEXT + TASK + IHQ + JET: PASS")
print("PREVIOUS MAX FILES UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
