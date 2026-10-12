python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
source = p.read_text()
tree = ast.parse(source)
out = []

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in (
        "preprocess", "predict_raw", "postprocess"
    ):
        out.append(f"\n===== {node.name} =====\n")
        out.append(ast.get_source_segment(source, node) + "\n")

target = Path("/tmp/cta_pipeline_inspection.txt")
target.write_text("\n".join(out))

print("Saved full inspection:", target)
print("Total lines:", len(target.read_text().splitlines()))
print("\n===== FIRST 40 LINES =====")
for i, line in enumerate(target.read_text().splitlines()[:40], 1):
    print(f"{i}: {line}")

print("\nOriginal project files unchanged.")
PY
