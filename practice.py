python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
src = p.read_text()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "predict_raw":
        lines = src.splitlines()
        print("===== PREDICT_RAW: MODEL CALLS =====")
        print("Function lines:", node.lineno, "-", node.end_lineno)

        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            name = ast.unparse(call.func)
            if any(x in name.lower() for x in
                   ("model", "predict", "forward", "preprocess", "postprocess")):
                print("\nCALL:", name, "| line:", call.lineno)
                for n in range(max(node.lineno, call.lineno-2),
                               min(node.end_lineno, call.end_lineno+2)+1):
                    if n-call.lineno < 12:
                        print(f"{n}: {lines[n-1]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
