python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in (
    "grecbase_max.py",
    "grecbase_fusion_graph_max.py",
):
    p = base / filename
    print(f"\n===== {filename} =====")

    if not p.exists():
        print("FILE NOT FOUND")
        continue

    tree = ast.parse(p.read_text())

    print("DEFINITIONS:")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            print(" ", node.name)
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name in (
                        "__init__", "__call__", "forward"
                    ):
                        print("   ", child.name, ast.unparse(child.args))

    print("GRAPH INPUTS / OUTPUTS:")
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("input", "output"):
                print(" ", node.lineno, ast.unparse(node)[:180])
                count += 1
                if count >= 16:
                    print("  ... remaining calls omitted")
                    break

print("\nREAD ONLY — ORIGINAL CODE UNCHANGED")
PY
