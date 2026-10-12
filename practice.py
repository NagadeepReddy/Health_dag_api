podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast
import sys
from pathlib import Path

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
source_file = base / "grecbase_fusion_all8_max.py"
target = base / "grecbase_fusion_real_shapes_max.py"
real_input = base / "real_sanity_model_in.pt"

assert source_file.is_file()
assert real_input.is_file(), "Saved real inputs missing"

sys.path.insert(0, str(root))

tree = ast.parse(source_file.read_text())

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_all8"
]
assert len(builders) == 1
builders[0].name = "build_grecbase_fusion_graph_real_shapes"

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

# Original sequence length 4 -> real length 50.
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
assert len(groups) == 1

old = [ast.literal_eval(x.args[1]) for x in groups[0].elts]
assert old == [
    [1, 4], [1, 4], [1, 4],
    [1, 4, 1], [1, 1, 4, 256]
], old

new = [
    [1, 50], [1, 50], [1, 50],
    [1, 50, 1], [1, 1, 50, 256]
]

for node, shape in zip(groups[0].elts, new):
    node.args[1] = ast.parse(repr(shape), mode="eval").body

# NLP length 8 -> 5.
# IHQ and JET length 1 -> 50.
changes = {"nlp": 0, "aux": 0}

for node in ast.walk(kw.value):
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "TensorType"
    ):
        continue

    shape = ast.literal_eval(node.args[1])

    if shape == [1, 8]:
        node.args[1] = ast.parse("[1, 5]", mode="eval").body
        changes["nlp"] += 1

    elif shape == [1, 1]:
        node.args[1] = ast.parse("[1, 50]", mode="eval").body
        changes["aux"] += 1

assert changes == {"nlp": 2, "aux": 3}, changes

# Change the NLP forward length argument.
nlp_calls = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "nlp_bert_forward"
]
assert len(nlp_calls) == 1
assert ast.literal_eval(nlp_calls[0].args[-1]) == 8
nlp_calls[0].args[-1] = ast.Constant(5)

# Original request contains 10 siblings, not 3.
sibling_comps = [
    n for n in ast.walk(kw.value)
    if isinstance(n, ast.ListComp)
    and len(n.generators) == 2
    and ast.unparse(n.generators[0].iter) == "range(3)"
]
assert len(sibling_comps) == 1

sibling_comps[0].generators[0].iter = ast.parse(
    "range(10)", mode="eval"
).body

sibling_loops = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.For)
    and "sibling_inputs" in ast.unparse(n)
    and "sibling_outputs.append" in ast.unparse(n)
]
assert len(sibling_loops) == 1
assert ast.unparse(sibling_loops[0].iter) == "range(3)"

sibling_loops[0].iter = ast.parse(
    "range(10)", mode="eval"
).body

# Remaining inputs: context 18 + NLP 2 +
# sequence 5 + siblings 40 = 65.
assertions = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.Assert)
    and "len(remaining)" in ast.unparse(n.test)
]
assert len(assertions) == 1
assert ast.unparse(assertions[0].test) == "len(remaining) == 37"
assertions[0].test.comparators[0] = ast.Constant(65)

slices = [
    n for n in ast.walk(builders[0])
    if isinstance(n, ast.Assign)
    and any(
        isinstance(t, ast.Name) and t.id == "sibling_inputs"
        for t in n.targets
    )
]
assert len(slices) == 1
assert ast.unparse(slices[0].value) == "remaining[25:37]"
slices[0].value.slice.upper = ast.Constant(65)

updated = ast.unparse(
    ast.fix_missing_locations(tree)
) + "\n"

code = compile(updated, str(target), "exec")

namespace = {
    "__file__": str(target),
    "__name__": "cta_max.real_shapes_validation",
    "__package__": "cta_max",
}

exec(code, namespace)

print("REAL INPUT LENGTHS CONFIGURED")
print("SEQUENCE: 50")
print("NLP: 5")
print("IHQ / JET: 50")
print("SIBLINGS: 10")
print("PYTHON SYNTAX: PASS", flush=True)

from max.graph import DeviceRef

graph = namespace[
    "build_grecbase_fusion_graph_real_shapes"
](DeviceRef.CPU())

print("REAL-SHAPE GRAPH CONSTRUCTION: PASS")

if target.exists():
    assert target.read_text() == updated, (
        "Existing target differs; refusing overwrite"
    )
else:
    target.write_text(updated)

print("REAL-SHAPE MAX GRAPH SAVED")
print("PREVIOUS WORKING GRAPH UNCHANGED")
print("ORIGINAL DS AND PYTORCH CODE UNCHANGED")
PY
