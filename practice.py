python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src = b / "parallel_transformer_block_multilayer.py"
dst = b / "parallel_transformer_block_2layers.py"
graph = b / "parallel_transformer_graph_2layers.py"

assert src.is_file() and graph.is_file()
assert not dst.exists(), "STOP: target already exists"

s = src.read_text()
tree = ast.parse(s)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
           and n.name == "ParallelTransformerBlockMAX")

init = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
            and n.name == "__init__")
call = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
            and n.name == "__call__")

norm = [n for n in init.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Attribute) and t.attr == "norm1"
                for t in n.targets)]
use = [n for n in ast.walk(call) if isinstance(n, ast.Assign)
       and any(isinstance(t, ast.Name) and t.id == "x_norm"
               for t in n.targets)]

assert len(norm) == len(use) == 1, "STOP: norm1 structure differs"
assert ast.unparse(use[0].value) == "self.norm1(x)", "STOP: norm1 call differs"

lines = s.splitlines()
indent = " " * use[0].col_offset

replacement = f'''
{indent}norm1_g = ops.constant(
{indent}    np.load(
{indent}        "artifacts/v1.168-max/cta_max/sequence_weights/"
{indent}        + ("fn_norm1_g.npy" if self.layer_idx == 0 else "fn_norm1_g_layer1.npy")
{indent}    ).astype(np.float32),
{indent}    dtype=x.dtype,
{indent}    device=DeviceRef.CPU(),
{indent})
{indent}variance1 = ops.mean(x * x, axis=-1)
{indent}x_norm = x * ops.rsqrt(variance1 + 1e-6) * norm1_g
'''.strip("\n").splitlines()

edits = [
    (norm[0].lineno, norm[0].end_lineno, []),
    (use[0].lineno, use[0].end_lineno, replacement),
]
for start, end, repl in sorted(edits, reverse=True):
    lines[start-1:end] = repl

updated = "\n".join(lines) + "\n"
ast.parse(updated)

gs = graph.read_text()
old = "from parallel_transformer_block_multilayer import ParallelTransformerBlockMAX"
assert gs.count(old) == 1, "STOP: graph import differs"
gs = gs.replace(old, "from parallel_transformer_block_2layers import ParallelTransformerBlockMAX")
ast.parse(gs)

dst.write_text(updated)
graph.write_text(gs)

print("TWO-LAYER NORM1 ISOLATION READY — SYNTAX OK")
print("BLOCK-0, BLOCK-1 AND DS CODE UNCHANGED")
PY
