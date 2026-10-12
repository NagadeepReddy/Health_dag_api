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

found = {}

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    if not isinstance(node.func, ast.Attribute):
        continue
    if node.func.attr != "reshape":
        continue
    if not isinstance(node.func.value, ast.Name):
        continue

    name = node.func.value.id
    if name not in ("q", "k", "v"):
        continue

    args = node.args
    if len(args) == 1 and isinstance(args[0], (ast.Tuple, ast.List)):
        dims = args[0].elts
    else:
        dims = args

    if len(dims) != 4:
        continue

    if (
        ast.unparse(dims[0]) == f"{name}.shape[0]"
        and ast.unparse(dims[2]) == f"{name}.shape[1]"
        and ast.unparse(dims[3]) == "256"
    ):
        assert name not in found, f"STOP: duplicate {name}"
        found[name] = dims[1]

assert set(found) == {"q", "k", "v"}, \
    f"STOP: unexpected reshapes: {sorted(found)}"

assert ast.literal_eval(found["q"]) == 2
assert ast.literal_eval(found["k"]) == 1
assert ast.literal_eval(found["v"]) == 1

# Only change Q. K and V are already correct.
q = found["q"]

lines = source.splitlines(keepends=True)
start = sum(len(x) for x in lines[:q.lineno-1]) + q.col_offset
end = sum(len(x) for x in lines[:q.end_lineno-1]) + q.end_col_offset

assert source[start:end] == "2"

updated = source[:start] + "1" + source[end:]
ast.parse(updated)

assert "self.heads = 1" in updated
assert "[256, 256, 256, 2048]" in updated

p.write_text(updated)

print("Q HEAD CORRECTED: 2 -> 1")
print("K AND V PRESERVED: 1 HEAD")
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
    "cta_attention_one_head_corrected",
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
