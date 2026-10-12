podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import ast
import sys
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/att_pooling_max.py")
source = p.read_text()
tree = ast.parse(source)

fixes = {}

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        continue

    target = node.targets[0]
    if not isinstance(target, ast.Name) or target.id not in ("q", "k", "v"):
        continue

    name = target.id
    call = node.value

    if not (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "reshape"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == name
        and len(call.args) == 1
        and isinstance(call.args[0], (ast.Tuple, ast.List))
    ):
        continue

    dims = call.args[0].elts

    if (
        len(dims) == 4
        and ast.unparse(dims[0]) == f"{name}.shape[0]"
        and ast.unparse(dims[2]) == f"{name}.shape[1]"
        and isinstance(dims[1], ast.Constant)
        and dims[1].value == 2
        and isinstance(dims[3], ast.Constant)
        and dims[3].value == 256
    ):
        assert name not in fixes, f"STOP: duplicate {name} reshape"
        fixes[name] = dims[1]

assert set(fixes) == {"q", "k", "v"}, (
    f"STOP: expected q/k/v reshapes; found {sorted(fixes)}"
)

lines = source.splitlines(keepends=True)
offsets = [0]
for line in lines:
    offsets.append(offsets[-1] + len(line))

edits = []
for name, node in fixes.items():
    start = offsets[node.lineno - 1] + node.col_offset
    end = offsets[node.end_lineno - 1] + node.end_col_offset
    assert source[start:end] == "2"
    edits.append((start, end))

updated = source
for start, end in sorted(edits, reverse=True):
    updated = updated[:start] + "self.heads" + updated[end:]

ast.parse(updated)
assert "self.heads = 1" in updated
assert "[256, 256, 256, 2048]" in updated

p.write_text(updated)
print("Q/K/V RESHAPES CORRECTED — 1 HEAD")
print("SYNTAX PASS", flush=True)

sys.path.insert(0, str(p.parent))

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType
from att_pooling_max import AttPoolingBlockMAX

device = DeviceRef.from_device(CPU())
block = AttPoolingBlockMAX(
    dtype=DType.float32,
    device=device,
    layer_idx=0
)

graph = Graph(
    "cta_attention_one_head_shape_check",
    input_types=[
        TensorType(DType.float32, [1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ]
)

with graph:
    output = block(*graph.inputs)
    graph.output(output)

print("ATTENTION GRAPH CONSTRUCTION: PASS")
print("OUTPUT SHAPE:", output.shape)
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
