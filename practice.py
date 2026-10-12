podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import re
import sys

from max.driver import CPU
from max.dtype import DType
from max.graph import DeviceRef, Graph, TensorType

base = Path("artifacts/v1.168-max/cta_max")
p = base / "att_pooling_max.py"
source = p.read_text()

pattern = (
    r'q\.reshape\(\(\s*'
    r'q\.shape\[0\]\s*,\s*2\s*,\s*'
    r'q\.shape\[1\]\s*,\s*256\s*'
    r'\)\)'
)

replacement = (
    "q.reshape((q.shape[0], 1, q.shape[1], 256))"
)

updated, count = re.subn(pattern, replacement, source)

assert count == 1, (
    f"STOP: expected exactly one Q reshape, found {count}"
)

assert "self.heads = 1" in updated
assert "[256, 256, 256, 2048]" in updated

ast.parse(updated)

# Test corrected code in memory before saving.
sys.path.insert(0, str(base))

namespace = {
    "__name__": "att_pooling_preflight",
    "__file__": str(p),
}

exec(compile(updated, str(p), "exec"), namespace)

device = DeviceRef.from_device(CPU())

block = namespace["AttPoolingBlockMAX"](
    dtype=DType.float32,
    device=device,
    layer_idx=0,
)

graph = Graph(
    "cta_attention_q_fix_preflight",
    input_types=[
        TensorType(DType.float32, [1, 8, 256], device=device),
        TensorType(DType.float32, [1, 1, 8, 256], device=device),
    ],
)

with graph:
    output = block(*graph.inputs)
    graph.output(output)

print("GRAPH OUTPUT:", output.shape, flush=True)

assert len(output.shape) == 3
assert [int(d) for d in output.shape] == [1, 8, 256], (
    f"STOP: unexpected output shape {output.shape}"
)

p.write_text(updated)

print("Q HEAD FIX SAVED: 2 -> 1")
print("K AND V UNCHANGED")
print("ATTENTION GRAPH CONSTRUCTION: PASS")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
