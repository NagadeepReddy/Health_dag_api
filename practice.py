python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.167/core-artifact/pipeline.py"
)

assert p.is_file(), "STOP: Original pipeline missing"

source = p.read_text()
tree = ast.parse(source)

matches = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == "inference"
]

print("=== ORIGINAL CTA INFERENCE ===")

for node in matches:
    print(f"LINES: {node.lineno}-{node.end_lineno}")
    for number in range(node.lineno, node.end_lineno + 1):
        print(f"{number}: {source.splitlines()[number-1]}")

print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
