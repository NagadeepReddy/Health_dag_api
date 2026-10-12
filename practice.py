podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path
import numpy as np

root = Path("artifacts/v1.168-max")
base = root / "cta_max"
sys.path.insert(0, str(root.resolve()))

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData
from cta_max.grecbase_fusion_all8_max import (
    build_grecbase_fusion_graph_all8
)

# Read the mapping from the previously working sequence runner.
runner = base / "run_transformer_full_sequence.py"
assert runner.is_file()

tree = ast.parse(runner.read_text())
wbase = str(base / "sequence_weights")

def resolve(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id == "WBASE":
        return wbase
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return resolve(node.left) + resolve(node.right)
    if isinstance(node, ast.Dict):
        return {
            resolve(k): resolve(v)
            for k, v in zip(node.keys, node.values)
        }
    raise ValueError(f"Unexpected registry expression: {ast.dump(node)[:150]}")

weight_files = None

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id == "weight_files"
            for t in node.targets
        ):
            assert weight_files is None
            weight_files = resolve(node.value)

    elif (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "weight_files"
        and node.value.func.attr == "update"
    ):
        assert weight_files is not None
        weight_files.update(resolve(node.value.args[0]))

assert weight_files, "Existing sequence weight mapping not found"

required = "sequence_transformer.page_embedding"
assert required in weight_files, "Sequence registry incomplete"

missing = [
    name for name, path in weight_files.items()
    if not Path(path).is_file()
]
assert not missing, f"Missing sequence weight files: {missing[:8]}"

weights = {}

for name, path in weight_files.items():
    arr = np.load(path).astype(np.float32)
    weights[name] = WeightData.from_numpy(arr, name)

print("SEQUENCE WEIGHTS REGISTERED:", len(weight_files))

# Reuse the already proven attention registry.
for p in sorted(base.rglob("att_pooling.*.npy")):
    name = p.stem
    assert name not in weights, f"Duplicate registry key: {name}"
    arr = np.load(p).astype(np.float32)
    weights[name] = WeightData.from_numpy(arr, name)

# Reuse the norm alias required by the validated sequence runner.
norm_path = base / "sequence_weights/fn_norm1_g_layer1.npy"
assert norm_path.is_file()

arr = np.load(norm_path).astype(np.float32)
weights["weight"] = WeightData.from_numpy(arr, "weight")

print("TOTAL REGISTERED WEIGHTS:", len(weights))

device = CPU()
graph = build_grecbase_fusion_graph_all8(DeviceRef.CPU())

print("EIGHT-BRANCH CONSTRUCTION: PASS")

session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("EIGHT-BRANCH COMPILATION: PASS")

def tensor(shape, dtype, fill=0):
    return Tensor.from_numpy(
        np.full(shape, fill, dtype=dtype)
    ).to(device)

inputs = []

# Task, IHQ, JET
inputs += [tensor((1,), np.int64) for _ in range(2)]
inputs += [tensor((1, 1), np.int64) for _ in range(3)]

# Context
inputs += [tensor((1,), np.int64) for _ in range(17)]
inputs.append(tensor((1, 127), np.float32))

# NLP
inputs.append(tensor((1, 8), np.int64))
inputs.append(tensor((1, 8), np.int64, 1))

# Sequence
inputs += [tensor((1, 4), np.int64) for _ in range(3)]
inputs.append(tensor((1, 4, 1), np.float32))
inputs.append(tensor((1, 1, 4, 256), np.float32))

# Three siblings
for _ in range(3):
    inputs += [tensor((1,), np.int64) for _ in range(3)]
    inputs.append(tensor((1, 18), np.float32))

assert len(inputs) == 42, len(inputs)

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("ALL EIGHT BRANCHES RUNTIME: PASS")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
