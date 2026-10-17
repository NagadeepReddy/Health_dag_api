
python3 - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in ["live_cta_pipeline_bridge.py", "serve_max.py"]:
    p = base / filename
    print(f"\n=== {filename} ===")
    if not p.is_file():
        print("NOT FOUND")
        continue

    tree = ast.parse(p.read_text())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            print(f"FUNCTION line {node.lineno}: {node.name}")
        elif isinstance(node, ast.ClassDef):
            print(f"CLASS line {node.lineno}: {node.name}")
PY
