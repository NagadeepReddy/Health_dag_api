python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

assert p.is_file(), "STOP: Adapter missing"
source = p.read_text()
tree = ast.parse(source)

print("=== DEVELOPMENT BATCH ADAPTER ===")

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "predict_batch":
            print(f"METHOD: {node.name}")
            print(f"LINES: {node.lineno}-{node.end_lineno}")

            lines = source.splitlines()
            for n in range(node.lineno, node.end_lineno + 1):
                print(f"{n:4}: {lines[n-1]}")

            print("ADAPTER SYNTAX: PASS")
            print("NO FILES MODIFIED")
            break
else:
    raise RuntimeError("predict_batch method missing")
PY
