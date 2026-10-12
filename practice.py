python - <<'PY'
import ast
import json
from pathlib import Path

root = Path("artifacts/v1.168")
pipeline = root / "core-artifact/pipeline.py"
models = root / "utils/dependency-utils/models.py"

assert pipeline.is_file()
assert models.is_file()

print("===== ORIGINAL PIPELINE METHODS =====")
tree = ast.parse(pipeline.read_text())

for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef):
        for method in cls.body:
            if isinstance(method, ast.FunctionDef):
                if any(k in method.name.lower() for k in (
                    "preprocess", "predict", "postprocess",
                    "forward", "process"
                )):
                    print(cls.name, method.name,
                          ast.unparse(method.args))

print("\n===== ORIGINAL GRecBase INPUTS =====")
tree = ast.parse(models.read_text())

for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == "GRecBase":
        for method in cls.body:
            if isinstance(method, ast.FunctionDef) and method.name == "forward":
                print(ast.unparse(method.args))

print("\n===== REAL SANITY INPUT STRUCTURE =====")

candidates = list(Path(".").rglob("sanity_input.json"))
print("FILES FOUND:", len(candidates))

def describe(value):
    if isinstance(value, dict):
        return f"object ({len(value)} keys)"
    if isinstance(value, list):
        sample = type(value[0]).__name__ if value else "empty"
        return f"list length={len(value)}, element={sample}"
    return type(value).__name__

for path in candidates[:3]:
    print("FILE:", path)
    data = json.loads(path.read_text())

    if isinstance(data, dict):
        for key, value in data.items():
            print(" ", key, ":", describe(value))
    else:
        print("ROOT:", describe(data))

print("\nREAL INPUT CONTRACT CHECK COMPLETE")
print("NO FILES MODIFIED")
PY
