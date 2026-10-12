python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/grecbase_max.py")
source = p.read_text()
tree = ast.parse(source)

cls = next(
    n for n in tree.body
    if isinstance(n, ast.ClassDef)
    and n.name == "GRecBaseMAX"
)

print("===== EXISTING GRecBaseMAX CONSTRUCTOR =====")

for node in cls.body:
    if isinstance(node, ast.FunctionDef) and node.name == "__init__":
        print(ast.get_source_segment(source, node))

print("\n===== IMPORTS =====")

for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        print(ast.get_source_segment(source, node))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
