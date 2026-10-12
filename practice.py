podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType

base = Path("artifacts/v1.168-max/cta_max")
p = base / "att_pooling_max.py"
s = p.read_text()

changes = {
    "q.reshape((q.shape[0], 2, q.shape[1], 256))":
    "q.reshape((q.shape[0], 1, q.shape[1], 256))",

    "out.reshape([out.shape[0], out.shape[2], 512])":
    "out.reshape([out.shape[0], out.shape[2], 256])",
}

for old, new in changes.items():
    assert s.count(old) == 1, f"STOP: code differs: {old}"
    s = s.replace(old, new, 1)

assert "self.heads = 1" in s
assert "[256, 256, 256, 2048]" in s
ast.parse(s)

# Test modified code WITHOUT saving first.
sys.path.insert(0, str(base))

ns = {
    "__name__": "att_pooling_preflight",
    "__file__": str(p),
}

exec(compile(s, str(p), "exec"), ns)

device = DeviceRef.from_device(CPU())

block = ns["AttPoolingBlockMAX"](
    dtype=DType.float32,
    device=device,
    layer_idx=0,
)

graph = Graph(
    "cta_attention_shape_preflight",
    input_types=[
        TensorType(DType.float32, [1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ],
)

with graph:
    output = block(*graph.inputs)
    graph.output(output)

print("GRAPH OUTPUT:", output.shape, flush=True)

assert all(
    int(dim) == expected
    for dim, expected in zip(output.shape, (1, 8, 256))
), "STOP: unexpected output dimensions"
assert len(output.shape) == 3

p.write_text(s)

print("Q HEAD CORRECTED: 1")
print("ATTENTION OUTPUT DIMENSION: 256")
print("ATTENTION GRAPH CONSTRUCTION: PASS")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY
