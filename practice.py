python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
p = base / "att_pooling_max.py"
tree = ast.parse(p.read_text())

print("=== ATTENTION POOLING IMPORT CHECK ===")
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        imports = [
            n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Import)
            and any(a.name == "numpy" for a in n.names)
        ]
        if imports:
            print(f"{node.name}: local numpy imports at {imports}")

print("\n=== ORIGINAL PYTORCH POOLING USAGE ===")
src = Path("artifacts/v1.168/utils/dependency-utils/models.py")
lines = src.read_text().splitlines()
matches = [
    i for i, line in enumerate(lines)
    if "ihq_pooling" in line or "jet_pooling" in line
]
if not matches:
    print("No direct pooling references found")
for i in matches:
    print(f"\n--- Original source around line {i+1} ---")
    for j in range(max(0, i-4), min(len(lines), i+5)):
        print(f"{j+1}: {lines[j]}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
