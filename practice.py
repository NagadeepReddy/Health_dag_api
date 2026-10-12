python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
source = p.read_text()
lines = source.splitlines()
tree = ast.parse(source)

found = False
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "inference":
        found = True
        print("INFERENCE METHOD:", node.lineno, "-", node.end_lineno)
        print("ARGUMENTS:", ast.unparse(node.args))
        print("\nFIRST 50 LINES:")
        for i in range(node.lineno, min(node.end_lineno, node.lineno + 49) + 1):
            print(f"{i}: {lines[i-1]}")

if not found:
    print("INFERENCE METHOD NOT DEFINED IN pipeline.py")
    print("May be inherited from another module.")

print("\nNO FILES MODIFIED")
PY
