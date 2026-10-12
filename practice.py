python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src0 = b / "run_transformer_max.py"
src1 = b / "run_transformer_layer1.py"
dst = b / "run_transformer_2layers.py"

assert not dst.exists(), "STOP: combined runner already exists"

def get_weights(path):
    s = path.read_text()
    tree = ast.parse(s)
    nodes = [
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "weight_files"
                for t in n.targets)
    ]
    assert len(nodes) == 1, f"STOP: weight registry differs: {path.name}"
    entries = {}
    for k, v in zip(nodes[0].value.keys, nodes[0].value.values):
        assert isinstance(k, ast.Constant) and isinstance(k.value, str)
        entries[k.value] = ast.get_source_segment(s, v)
    return entries

w0 = get_weights(src0)
w1 = get_weights(src1)

assert len(w0) == len(w1) == 5
assert all(".ptransformer.0." in k for k in w0)
assert all(".ptransformer.1." in k for k in w1)
assert not (w0.keys() & w1.keys())

s = src1.read_text()
old = "from parallel_transformer_graph_layer1 import build_parallel_transformer_graph"
assert s.count(old) == 1, "STOP: graph import differs"

s = s.replace(
    old,
    "from parallel_transformer_graph_2layers import build_parallel_transformer_graph",
    1
)

tree = ast.parse(s)
node = next(
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "weight_files"
            for t in n.targets)
)

entries = {**w0, **w1}
replacement = "weight_files = {\n" + "".join(
    f"    {k!r}: {v},\n" for k, v in entries.items()
) + "}"

lines = s.splitlines()
lines[node.lineno-1:node.end_lineno] = replacement.splitlines()
s = "\n".join(lines) + "\n"

tree = ast.parse(s)

saves = [
    n for n in tree.body
    if isinstance(n, ast.Expr)
    and isinstance(n.value, ast.Call)
    and ast.unparse(n.value.func) == "np.save"
    and len(n.value.args) >= 2
    and ast.unparse(n.value.args[1]) == "max_out"
]

refs = [
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "pt_out"
            for t in n.targets)
]

assert len(saves) == 1, "STOP: MAX save structure differs"
assert len(refs) == 1, "STOP: parity reference differs"
assert saves[0].end_lineno < refs[0].lineno

lines = s.splitlines()
lines[saves[0].lineno-1:saves[0].end_lineno] = [
    'np.save(BASE + "/transformer_max_output_2layers.npy", max_out)'
]

s = "\n".join(lines[:refs[0].lineno-1]) + "\n"
s += 'print("TWO-LAYER MAX SHAPE:", max_out.shape)\n'
s += 'print("FINITE:", bool(np.isfinite(max_out).all()))\n'

ast.parse(s)
dst.write_text(s)

print("TWO-LAYER RUNNER CREATED — SYNTAX OK")
print("REGISTERED WEIGHTS:", len(entries))
print("BLOCK-0, BLOCK-1 AND DS CODE UNCHANGED")
PY
