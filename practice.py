python3 - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
graph_file = base / "grecbase_fusion_order_correct_max_branch_diag.py"
block_file = base / "parallel_transformer_block_2layers.py"

for p in (graph_file, block_file):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing {p}")

graph = ast.parse(graph_file.read_text())
block = ast.parse(block_file.read_text())

print("=== GRAPH TRANSFORMER IMPORT ===")
for n in ast.walk(graph):
    if isinstance(n, ast.ImportFrom):
        if any(a.name == "ParallelTransformerBlockMAX" for a in n.names):
            print(n.lineno, "from", n.module)

print("\n=== GRAPH TRANSFORMER CALLS ===")
for n in ast.walk(graph):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        if n.func.id in ("block0", "block1"):
            print(n.lineno, ast.unparse(n))

print("\n=== TRANSFORMER SIGNATURE AND ATTENTION ===")
for cls in ast.walk(block):
    if isinstance(cls, ast.ClassDef) and cls.name == "ParallelTransformerBlockMAX":
        for fn in cls.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == "__call__":
                print("Arguments:", [a.arg for a in fn.args.args])
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call):
                        expression = ast.unparse(n)
                        if any(x in expression for x in
                               ("softmax", "masked_fill", "where(", "valid_length")):
                            print("Line", n.lineno, expression[:180])
PY
