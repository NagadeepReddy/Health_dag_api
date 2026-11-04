cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.472/core-artifact/pipeline.py")
lines = p.read_text().splitlines()
tree = ast.parse("\n".join(lines))

print("=== ORIGINAL DS INFERENCE CONTRACT ===")

for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name in (
        "preprocess", "inference", "predict",
        "predict_raw", "postprocess", "__call__"
    ):
        print(f"METHOD {n.lineno}: {n.name}({ast.unparse(n.args)})")

print("\n=== ORIGINAL INFERENCE CALL SITES ===")
for i, line in enumerate(lines):
    if any(s in line for s in (
        "self.inference(", ".inference(",
        "def predict(", "def predict_raw("
    )):
        print(f"\nLINE {i+1}")
        for j in range(max(0, i-4), min(len(lines), i+9)):
            print(f"{j+1}: {lines[j]}")

print("\nINSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
PY
