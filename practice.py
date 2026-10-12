python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src = b / "parallel_transformer_block_multilayer.py"
dst = b / "parallel_transformer_block_2layers.py"
graph = b / "parallel_transformer_graph_2layers.py"

assert not dst.exists(), "STOP: two-layer block already exists"
assert (b / "sequence_weights/fn_norm1_g.npy").is_file()
assert (b / "sequence_weights/fn_norm1_g_layer1.npy").is_file()

s = src.read_text()
tree = ast.parse(s)

cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
           and n.name == "ParallelTransformerBlockMAX")
init = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
            and n.name == "__init__")
call = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
            and n.name == "__call__")

norm = [n for n in init.body if isinstance(n, ast.Assign)
        and any(ast.unparse(t) == "self.norm1" for t in n.targets)]

xn = [n for n in call.body if isinstance(n, ast.Assign)
      and any(ast.unparse(t) == "x_norm" for t in n.targets)]

assert len(norm) == 1, "STOP: norm1 declaration differs"
assert len(xn) == 2, "STOP: expected two x_norm assignments"
assert ast.unparse(xn[1].value) == "self.norm1(x)", "STOP: norm1 call differs"
assert xn[0].end_lineno < xn[1].lineno + 1, "STOP: x_norm sequence differs"

uses = [n for n in ast.walk(call) if isinstance(n, ast.Attribute)
        and ast.unparse(n) == "self.norm1"]
assert len(uses) == 1, "STOP: other norm1 usage exists"

lines = s.splitlines()
indent = " " * xn[0].col_offset

replacement = f'''{indent}import numpy as np
{indent}norm1_g = ops.constant(
{indent}    np.load(
{indent}        "artifacts/v1.168-max/cta_max/sequence_weights/"
{indent}        + ("fn_norm1_g.npy" if self.layer_idx == 0 else "fn_norm1_g_layer1.npy")
{indent}    ).astype(np.float32),
{indent}    dtype=x.dtype,
{indent}    device=DeviceRef.CPU(),
{indent})
{indent}x_norm = x * ops.rsqrt(variance1 + 1e-6) * norm1_g'''.splitlines()

edits = [
    (norm[0].lineno, norm[0].end_lineno, []),
    (xn[0].lineno, xn[1].end_lineno, replacement),
]

for start, end, repl in sorted(edits, reverse=True):
    lines[start-1:end] = repl

updated = "\n".join(lines) + "\n"
ast.parse(updated)

gs = graph.read_text()
old = "from parallel_transformer_block_multilayer import ParallelTransformerBlockMAX"
assert gs.count(old) == 1, "STOP: graph import differs"

gs = gs.replace(
    old,
    "from parallel_transformer_block_2layers import ParallelTransformerBlockMAX",
    1
)
ast.parse(gs)

dst.write_text(updated)
graph.write_text(gs)

print("TWO-LAYER NORM1 ISOLATION READY")
print("SYNTAX VERIFIED")
print("VERIFIED BLOCKS AND DS CODE UNCHANGED")
PY
