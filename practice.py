python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py")
lines = p.read_text().splitlines()
tree = ast.parse("\n".join(lines))

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "predict_raw":
        print(f"\n=== ORIGINAL DS predict_raw(): {node.lineno}-{node.end_lineno} ===")
        for i in range(max(node.lineno, node.end_lineno - 100), node.end_lineno + 1):
            print(f"{i}: {lines[i-1]}")
        break
else:
    print("predict_raw not found in pipeline.py")

print("\nORIGINAL DS FILE UNCHANGED")
PY
