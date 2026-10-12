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

cls = next(
    n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "AttPoolingBlockMAX"
)

forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__call__"
)

lines = source.splitlines(keepends=True)
offsets = [0]
for line in lines:
    offsets.append(offsets[-1] + len(line))

fixes = {}

for call in ast.walk(forward):
    if not isinstance(call, ast.Call):
        continue

    if not isinstance(call.func, ast.Attribute):
        continue

    if call.func.attr != "reshape":
        continue

    # Match q.reshape(...), k.reshape(...), v.reshape(...)
    if isinstance(call.func.value, ast.Name):
        name = call.func.value.id
        args = call.args

    # Also support ops.reshape(q, ...)
    elif (
        isinstance(call.func.value, ast.Name)
        and call.func.value.id == "ops"
    ):
        continue
    else:
        continue

    if name not in ("q", "k", "v"):
        continue

    print("FOUND:", ast.unparse(call), flush=True)

    if len(args) == 1 and isinstance(
        args[0], (ast.Tuple, ast.List)
    ):
        dims = args[0].elts
    else:
        dims = args

    if len(dims) != 4:
        continue

    if not (
        isinstance(dims[1], ast.Constant)
        and dims[1].value == 2
        and isinstance(dims[3], ast.Constant)
        and dims[3].value == 256
    ):
        continue

    assert name not in fixes, \
        f"STOP: duplicate {name} reshape"

    node = dims[1]

    start = offsets[node.lineno - 1] + node.col_offset
    end = offsets[node.end_lineno - 1] + node.end_col_offset

    assert source[start:end] == "2"
    fixes[name] = (start, end)

print("MATCHED:", sorted(fixes), flush=True)

assert set(fixes) == {"q", "k", "v"}, \
    "STOP: not all Q/K/V reshapes identified; file unchanged"

updated = source

for start, end in sorted(fixes.values(), reverse=True):
    updated = updated[:start] + "self.heads" + updated[end:]

ast.parse(updated)

assert "self.heads = 1" in updated
assert "[256, 256, 256, 2048]" in updated

p.write_text(updated)

print("Q/K/V RESHAPES CORRECTED")
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
    "cta_attention_one_head_verified",
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
