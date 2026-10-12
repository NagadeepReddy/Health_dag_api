podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.graph import DeviceRef

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "grecbase_fusion_all8_max.py"
)

assert p.exists(), "Eight-branch source not found"

tree = ast.parse(p.read_text())

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

candidates = [
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

assert len(candidates) == 1, (
    "Sequence input definitions not uniquely identified"
)

seq_inputs = candidates[0].elts

current = [
    ast.literal_eval(x.args[1])
    for x in seq_inputs
]

expected = [
    [1, 4],
    [1, 4, 1],
    [1, 4, 1],
    [1, 1, 4, 256],
    [1, 1, 4, 256],
]

correct = [
    [1, 4],
    [1, 4],
    [1, 4],
    [1, 4, 1],
    [1, 1, 4, 256],
]

assert current in (expected, correct), (
    f"Unexpected sequence contract: {current}"
)

for node, shape in zip(seq_inputs, correct):
    node.args[1] = ast.parse(
        repr(shape), mode="eval"
    ).body

updated = ast.unparse(
    ast.fix_missing_locations(tree)
) + "\n"

compile(updated, str(p), "exec")

namespace = {
    "__file__": str(p.resolve()),
    "__name__": "cta_max.all8_shape_validation",
    "__package__": "cta_max",
}

exec(compile(updated, str(p), "exec"), namespace)

print("SEQUENCE INPUT SHAPES:", correct)

graph = namespace[
    "build_grecbase_fusion_graph_all8"
](DeviceRef.CPU())

print("EIGHT-BRANCH GRAPH CONSTRUCTION: PASS")

if p.read_text() != updated:
    p.write_text(updated)

print("CORRECTED MAX GRAPH SAVED")
print("SIX-BRANCH GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
