python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
source = p.read_text()
tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name in ("preprocess", "predict_raw", "postprocess"):
            print(f"\n===== {node.name} =====")
            print(ast.get_source_segment(source, node))

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
