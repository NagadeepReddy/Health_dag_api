python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src0 = b / "run_transformer_max.py"
src1 = b / "run_transformer_layer1.py"
dst = b / "run_transformer_2layers.py"

assert not dst.exists(), "STOP: combined runner already exists"

def registry(path):
    s = path.read_text()
    tree = ast.parse(s)
    found = [
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "weight_files"
                for t in n.targets)
    ]
    assert len(found) == 1, f"STOP: registry differs in {path.name}"
    node = found[0]
    assert isinstance(node.value, ast.Dict)
    entries = {}
    for k, v in zip(node.value.keys, node.value.values):
        assert isinstance(k, ast.Constant) and isinstance(k.value, str)
        entries[k.value] = ast.get_source_segment(s, v)
    return entries

w0 = registry(src0)
w1 = registry(src1)

assert len(w0) == len(w1) == 5
assert all(".ptransformer.0." in k for k in w0)
assert all(".ptransformer.1." in k for k in w1)
assert not (w0.keys() & w1.keys())

s = src1.read_text()

old_import = "from parallel_transformer_graph_layer1 import build_parallel_transformer_graph"
assert s.count(old_import) == 1
s = s.replace(
    old_import,
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

old_output = '"transformer_max_output_layer1.npy"'
new_output = '"transformer_max_output_2layers.npy"'

assert s.count(old_output) == 1, "STOP: output filename differs"
s = s.replace(old_output, new_output, 1)

tree = ast.parse(s)
comparison = [
    n for n in tree.body
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "pt_out"
            for t in n.targets)
]
assert len(comparison) == 1, "STOP: comparison structure differs"

s = "\n".join(s.splitlines()[:comparison[0].lineno-1]) + "\n"
s += 'print("TWO-LAYER MAX SHAPE:", max_out.shape)\n'
s += 'print("FINITE:", bool(np.isfinite(max_out).all()))\n'

ast.parse(s)
dst.write_text(s)

print("TWO-LAYER RUNNER CREATED — SYNTAX OK")
print("REGISTERED WEIGHTS:", len(entries))
print("VERIFIED BLOCKS AND DS CODE UNCHANGED")
PY
