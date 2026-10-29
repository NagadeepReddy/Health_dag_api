cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")

for p in root.rglob("pipeline.py"):
    if any(x in p.parts for x in (".git", "__pycache__", ".venv")):
        continue

    try:
        tree = ast.parse(p.read_text())
    except (SyntaxError, UnicodeError, OSError):
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "predict_raw":
                print("FILE:", p)
                print("LINES:", node.lineno, "-", node.end_lineno)
                lines = p.read_text().splitlines()
                for n in range(node.lineno, node.end_lineno + 1):
                    print(f"{n:4}: {lines[n-1]}")
                print("ORIGINAL DS: UNCHANGED")
                print("NO FILES MODIFIED")
                raise SystemExit(0)

print("NOT FOUND: predict_raw in repository pipeline.py files")
print("NO FILES MODIFIED")
PY
