podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import ast, sys
from pathlib import Path

root = Path("/workspace/artifacts/v1.168-max")
base = root / "cta_max"
source_file = base / "grecbase_fusion_all8_max.py"
target = base / "grecbase_fusion_real_shapes_max.py"

assert source_file.is_file()
assert (base / "real_sanity_model_in.pt").is_file()
sys.path.insert(0, str(root))

tree = ast.parse(source_file.read_text())

builders = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_grecbase_fusion_graph_all8"
]
assert len(builders) == 1
fn = builders[0]
fn.name = "build_grecbase_fusion_graph_real_shapes"

graphs = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "Graph"
]
assert len(graphs) == 1

kw = next(k for k in graphs[0].keywords if k.arg == "input_types")

def shape_of(call):
    return ast.literal_eval(call.args[1])

def set_shape(call, shape):
    call.args[1] = ast.parse(repr(shape), mode="eval").body

# Sequence: 4 -> 50.
groups = [
    n for n in ast.walk(kw.value)
    if isinstance(n, ast.List)
    and len(n.elts) == 5
    and all(isinstance(x, ast.Call) and
            isinstance(x.func, ast.Name) and
            x.func.id == "TensorType" for x in n.elts)
]
assert len(groups) == 1

old = [shape_of(n) for n in groups[0].elts]
assert old == [
    [1, 4], [1, 4], [1, 4],
    [1, 4, 1], [1, 1, 4, 256]
], old

for node, shape in zip(groups[0].elts, [
    [1, 50], [1, 50], [1, 50],
    [1, 50, 1], [1, 1, 50, 256]
]):
    set_shape(node, shape)

# One NLP template generates two real inputs.
# One auxiliary template generates three real inputs.
counts = {"nlp": 0, "aux": 0}

for n in ast.walk(kw.value):
    if not (isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "TensorType"):
        continue
    shape = shape_of(n)
    if shape == [1, 8]:
        set_shape(n, [1, 5])
        counts["nlp"] += 1
    elif shape == [1, 1]:
        set_shape(n, [1, 50])
        counts["aux"] += 1

assert counts == {"nlp": 1, "aux": 1}, counts

nlp_calls = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "nlp_bert_forward"
]
assert len(nlp_calls) == 1
assert ast.literal_eval(nlp_calls[0].args[-1]) == 8
nlp_calls[0].args[-1] = ast.Constant(5)

# Siblings: 3 -> 10.
comps = [
    n for n in ast.walk(kw.value)
    if isinstance(n, ast.ListComp)
    and len(n.generators) == 2
    and ast.unparse(n.generators[0].iter) == "range(3)"
]
assert len(comps) == 1
comps[0].generators[0].iter = ast.parse(
    "range(10)", mode="eval"
).body

loops = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.For)
    and "sibling_outputs.append" in ast.unparse(n)
    and "sibling_inputs" in ast.unparse(n)
]
assert len(loops) == 1
assert ast.unparse(loops[0].iter) == "range(3)"
loops[0].iter = ast.parse("range(10)", mode="eval").body

# 18 context + 2 NLP + 5 sequence + 40 sibling inputs.
checks = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Assert)
    and "len(remaining)" in ast.unparse(n.test)
]
assert len(checks) == 1
assert ast.unparse(checks[0].test) == "len(remaining) == 37"
checks[0].test.comparators[0] = ast.Constant(65)

assignments = [
    n for n in ast.walk(fn)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and
            t.id == "sibling_inputs" for t in n.targets)
]
assert len(assignments) == 1
assert ast.unparse(assignments[0].value) == "remaining[25:37]"
assignments[0].value.slice.upper = ast.Constant(65)

updated = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
code = compile(updated, str(target), "exec")

namespace = {
    "__file__": str(target),
    "__name__": "cta_max.real_shapes_check",
    "__package__": "cta_max",
}
exec(code, namespace)

from max.graph import DeviceRef
graph = namespace[
    "build_grecbase_fusion_graph_real_shapes"
](DeviceRef.CPU())

print("REAL-SHAPE GRAPH CONSTRUCTION: PASS")
print("SEQUENCE: 50 | NLP: 5 | IHQ/JET: 50 | SIBLINGS: 10")

if target.exists():
    assert target.read_text() == updated, "Different target exists"
else:
    target.write_text(updated)

print("REAL-SHAPE GRAPH SAVED: PASS")
print("PREVIOUS EIGHT-BRANCH GRAPH UNCHANGED")
print("ORIGINAL DS CODE UNCHANGED")
PY
