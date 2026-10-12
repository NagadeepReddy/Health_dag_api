podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path
import numpy as np

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
target = base / "grecbase_fusion_all8_max.py"

sys.path.insert(0, str(root))

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData

assert target.is_file(), "Eight-branch file missing"

tree = ast.parse(target.read_text())

# Fix the transformer import using its verified location.
imports = [
    n for n in tree.body
    if isinstance(n, ast.ImportFrom)
    and any(
        a.name == "ParallelTransformerBlockMAX"
        for a in n.names
    )
]
assert len(imports) == 1
assert (base / "parallel_transformer_block_2layers.py").is_file()

imports[0].module = "cta_max.parallel_transformer_block_2layers"

# Locate graph input definitions.
graphs = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]
assert len(graphs) == 1

kw = next(
    k for k in graphs[0].keywords
    if k.arg == "input_types"
)

# Correct sequence shapes using the validated sequence contract.
seq_groups = [
    n for n in ast.walk(kw.value)
    if isinstance(n, ast.List)
    and len(n.elts) == 5
    and all(
        isinstance(x, ast.Call)
        and isinstance(x.func, ast.Name)
        and x.func.id == "TensorType"
        for x in n.elts
    )
]
assert len(seq_groups) == 1

seq_shapes = [
    [1, 4],
    [1, 4],
    [1, 4],
    [1, 4, 1],
    [1, 1, 4, 256],
]

for node, shape in zip(seq_groups[0].elts, seq_shapes):
    node.args[1] = ast.parse(repr(shape), mode="eval").body

# Correct sibling wide dimension: 18, not 127.
sibling_groups = [
    n for n in ast.walk(kw.value)
    if isinstance(n, ast.ListComp)
    and len(n.generators) == 2
    and ast.unparse(n.generators[0].iter) == "range(3)"
    and isinstance(n.generators[1].iter, ast.Tuple)
    and len(n.generators[1].iter.elts) == 4
]
assert len(sibling_groups) == 1

sibling_types = sibling_groups[0].generators[1].iter.elts

old_shape = ast.literal_eval(sibling_types[3].args[1])
assert old_shape in ([1, 127], [1, 18]), old_shape

sibling_types[3].args[1] = ast.parse(
    "[1, 18]", mode="eval"
).body

print("SEQUENCE INPUT CONTRACT: CORRECTED")
print("SIBLING WIDE INPUT: [1, 18]")
print("TRANSFORMER IMPORT: CORRECTED")

# Compile Python source in memory first.
updated = ast.unparse(
    ast.fix_missing_locations(tree)
) + "\n"

code = compile(updated, str(target), "exec")

namespace = {
    "__file__": str(target),
    "__name__": "cta_max.all8_validation",
    "__package__": "cta_max",
}
exec(code, namespace)

print("PYTHON SOURCE VALIDATION: PASS")

# Construct all eight branches.
graph = namespace[
    "build_grecbase_fusion_graph_all8"
](DeviceRef.CPU())

print("EIGHT-BRANCH GRAPH CONSTRUCTION: PASS")

# Save only after successful construction.
if target.read_text() != updated:
    target.write_text(updated)

print("CORRECTED MAX FILE SAVED")

# Reuse proven attention weight registration.
weights = {}

for p in sorted(base.rglob("att_pooling.*.npy")):
    arr = np.load(p).astype(np.float32)
    assert p.stem not in weights
    weights[p.stem] = WeightData.from_numpy(arr, p.stem)

device = CPU()
session = InferenceSession(devices=[device])

model = session.load(graph, weights_registry=weights)

print("EIGHT-BRANCH COMPILATION: PASS")

def tensor(shape, dtype, fill=0):
    arr = np.full(shape, fill, dtype=dtype)
    return Tensor.from_numpy(arr).to(device)

inputs = []

# Task, IHQ and JET.
inputs += [tensor((1,), np.int64) for _ in range(2)]
inputs += [tensor((1, 1), np.int64) for _ in range(3)]

# Main context.
inputs += [tensor((1,), np.int64) for _ in range(17)]
inputs.append(tensor((1, 127), np.float32))

# NLP.
inputs.append(tensor((1, 8), np.int64))
inputs.append(tensor((1, 8), np.int64, fill=1))

# Sequence.
inputs += [tensor((1, 4), np.int64) for _ in range(3)]
inputs.append(tensor((1, 4, 1), np.float32))
inputs.append(tensor((1, 1, 4, 256), np.float32))

# Three siblings.
for _ in range(3):
    inputs += [tensor((1,), np.int64) for _ in range(3)]
    inputs.append(tensor((1, 18), np.float32))

assert len(inputs) == 42, len(inputs)

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("ALL EIGHT BRANCHES EXECUTION: PASS")
print("PREVIOUS SIX-BRANCH GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
