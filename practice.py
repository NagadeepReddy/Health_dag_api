podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import ast
from pathlib import Path

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
target = base / "grecbase_fusion_all8_max.py"

sys.path.insert(0, str(root))
sys.path.insert(0, str(base))

assert target.is_file(), "Eight-branch source missing"

tree = ast.parse(target.read_text())

# 1. Identify the existing incorrect block import.
imports = [
    node for node in tree.body
    if isinstance(node, ast.ImportFrom)
    and any(
        alias.name == "ParallelTransformerBlockMAX"
        for alias in node.names
    )
]

assert len(imports) == 1, (
    "Cannot uniquely identify transformer block import"
)

# 2. Find the actual class implementation.
candidates = []

for p in root.rglob("*.py"):
    if p == target:
        continue

    text = p.read_text()

    if "class ParallelTransformerBlockMAX" not in text:
        continue

    try:
        parsed = ast.parse(text)
    except SyntaxError:
        continue

    if any(
        isinstance(node, ast.ClassDef)
        and node.name == "ParallelTransformerBlockMAX"
        for node in parsed.body
    ):
        candidates.append(p)

# Prefer the implementation referenced by the
# previously validated full-sequence graph.
seq_file = base / "parallel_transformer_graph_full_sequence.py"
seq_tree = ast.parse(seq_file.read_text())

preferred = [
    node.module for node in seq_tree.body
    if isinstance(node, ast.ImportFrom)
    and any(
        alias.name == "ParallelTransformerBlockMAX"
        for alias in node.names
    )
]

if len(candidates) > 1 and len(preferred) == 1:
    matching = [
        p for p in candidates
        if p.stem == preferred[0].split(".")[-1]
    ]
    if len(matching) == 1:
        candidates = matching

print("TRANSFORMER CLASS CANDIDATES:",
      [str(p.relative_to(root)) for p in candidates])

assert len(candidates) == 1, (
    "Transformer class location is ambiguous; "
    "no changes made"
)

module = ".".join(
    candidates[0].relative_to(root).with_suffix("").parts
)

imports[0].module = module

print("CORRECTED IMPORT MODULE:", module)

# 3. Apply the previously confirmed sequence shapes.
graph_calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]

assert len(graph_calls) == 1

kw = next(
    k for k in graph_calls[0].keywords
    if k.arg == "input_types"
)

groups = [
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

assert len(groups) == 1, (
    "Sequence input group ambiguous; no changes made"
)

seq_inputs = groups[0].elts

old_shapes = [
    ast.literal_eval(n.args[1])
    for n in seq_inputs
]

correct_shapes = [
    [1, 4],
    [1, 4],
    [1, 4],
    [1, 4, 1],
    [1, 1, 4, 256],
]

previous_shapes = [
    [1, 4],
    [1, 4, 1],
    [1, 4, 1],
    [1, 1, 4, 256],
    [1, 1, 4, 256],
]

assert old_shapes in (previous_shapes, correct_shapes), (
    f"Unexpected sequence shapes: {old_shapes}"
)

for node, shape in zip(seq_inputs, correct_shapes):
    node.args[1] = ast.parse(
        repr(shape), mode="eval"
    ).body

print("SEQUENCE INPUT SHAPES:", correct_shapes)

# 4. Validate corrected source without modifying it.
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

print("EIGHT-BRANCH IMPORTS: PASS")
print("PYTHON SYNTAX: PASS")

# 5. Construct complete graph.
from max.graph import DeviceRef

builder = namespace["build_grecbase_fusion_graph_all8"]

graph = builder(DeviceRef.CPU())

print("EIGHT-BRANCH GRAPH CONSTRUCTION: PASS")

# Save only after successful construction.
if target.read_text() != updated:
    target.write_text(updated)

print("CORRECTED EIGHT-BRANCH GRAPH SAVED")
print("PREVIOUS SIX-BRANCH GRAPH UNCHANGED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
