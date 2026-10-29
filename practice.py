cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
import ast
from pathlib import Path

matches = list(Path(".").rglob("pipeline.py"))

for p in matches:
    if "artifacts" in p.parts:
        continue

    tree = ast.parse(p.read_text())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "predict_raw":
                print("FILE:", p)
                print("METHOD:", node.name)
                print("LINES:", node.lineno, "-", node.end_lineno)

                lines = p.read_text().splitlines()
                for n in range(node.lineno, node.end_lineno + 1):
                    print(f"{n:4}: {lines[n-1]}")

                print("ORIGINAL DS: UNCHANGED")
                raise SystemExit(0)

print("STOP: Original predict_raw not located")
PY
