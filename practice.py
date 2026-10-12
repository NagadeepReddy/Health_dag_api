podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
import re
from pathlib import Path
import numpy as np

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")

# Preserve the existing validated implementations.
aux_original = base / "grecbase_aux_features_max.py"
fusion_original = base / "grecbase_fusion_graph_max.py"

aux_new = base / "grecbase_aux_branches_max.py"
fusion_new = base / "grecbase_fusion_with_aux_max.py"

aux = aux_original.read_text()

old_return = "return ops.concat([task, ihq, jet], axis=1)"
assert aux.count(old_return) == 1, "Unexpected auxiliary source"

aux = aux.replace(old_return, "return task, ihq, jet")
ast.parse(aux)

fusion = fusion_original.read_text()

old_import = "from cta_max.att_pooling_max import AttPoolingBlockMAX"
assert fusion.count(old_import) == 1

fusion = fusion.replace(
    old_import,
    old_import +
    "\nfrom cta_max.grecbase_aux_branches_max import grecbase_aux_features"
)

old_function = "def build_grecbase_fusion_graph(device):"
assert fusion.count(old_function) == 1

fusion = fusion.replace(
    old_function,
    "def build_grecbase_fusion_graph_with_aux(device):"
)

# Five existing float branches + five real categorical inputs.
input_pattern = (
    r"input_types=\[\s*"
    r"TensorType\(DType\.float32,\s*\[1,\s*256\],\s*device=device\)"
    r"\s*for _ in range\(8\)\s*\]"
)

new_inputs = """input_types=(
            [TensorType(DType.float32, [1, 256], device=device)
             for _ in range(5)]
            +
            [TensorType(DType.int64, [1], device=device)
             for _ in range(2)]
            +
            [TensorType(DType.int64, [1, 1], device=device)
             for _ in range(3)]
        )"""

fusion, count = re.subn(input_pattern, new_inputs, fusion)
assert count == 1, f"Input modification failed: {count}"

old_stack = (
    r"outs\s*=\s*ops\.concat\(\s*"
    r"\[\s*ops\.reshape\(x,\s*\[1,\s*1,\s*256\]\)"
    r"\s*for x in graph\.inputs\s*\],"
    r"\s*axis=1,\s*\)"
)

new_stack = """seq, context, search0, search1, sibling, task0, task1, ihq_ids, jet_name, jet_status = graph.inputs

        task, ihq, jet = grecbase_aux_features(
            task0, task1, ihq_ids, jet_name, jet_status, device
        )

        # Preserve original GRecBase eight-branch ordering.
        outs = ops.concat(
            [
                ops.reshape(x, [1, 1, 256])
                for x in (
                    seq, context, search0, search1,
                    task, jet, ihq, sibling
                )
            ],
            axis=1,
        )"""

fusion, count = re.subn(old_stack, new_stack, fusion)
assert count == 1, f"Fusion modification failed: {count}"

ast.parse(fusion)

aux_new.write_text(aux)
fusion_new.write_text(fusion)

print("NEW MAX AUXILIARY CONNECTOR: CREATED")
print("NEW FUSION GRAPH: CREATED")

from cta_max.grecbase_fusion_with_aux_max import (
    build_grecbase_fusion_graph_with_aux
)

weights = {}

for p in sorted(base.rglob("att_pooling.*.npy")):
    arr = np.load(p).astype(np.float32)
    assert p.stem not in weights
    weights[p.stem] = WeightData.from_numpy(arr, p.stem)

device = CPU()

graph = build_grecbase_fusion_graph_with_aux(DeviceRef.CPU())
session = InferenceSession(devices=[device])

model = session.load(graph, weights_registry=weights)
print("REAL AUXILIARY FUSION COMPILATION: PASS")

inputs = [
    Tensor.from_numpy(np.zeros((1, 256), dtype=np.float32)).to(device)
    for _ in range(5)
]

inputs += [
    Tensor.from_numpy(np.zeros((1,), dtype=np.int64)).to(device)
    for _ in range(2)
]

inputs += [
    Tensor.from_numpy(np.zeros((1, 1), dtype=np.int64)).to(device)
    for _ in range(3)
]

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("TASK / IHQ / JET FUSION: PASS")
print("ORIGINAL FUSION AND DS CODE UNCHANGED")
PY
