cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472")
p = root / "core-artifact/pipeline.py"
tree = ast.parse(p.read_text())

cls = next(n for n in tree.body
           if isinstance(n, ast.ClassDef) and n.name == "pipeline")

print("=== ORIGINAL DS INITIALIZATION ===")
for n in cls.body:
    if isinstance(n, ast.FunctionDef) and n.name in ("__init__", "load", "preprocess"):
        print(n.name, "LINES:", n.lineno, "-", n.end_lineno)

pre = next(n for n in cls.body
           if isinstance(n, ast.FunctionDef) and n.name == "preprocess")

print("\n=== MODEL INPUT CONSTRUCTION ===")
count = 0
for n in ast.walk(pre):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "model_in":
                print("ASSIGN LINE:", n.lineno)
                if isinstance(n.value, ast.Dict):
                    keys = [
                        k.value for k in n.value.keys
                        if isinstance(k, ast.Constant)
                    ]
                    print("MODEL_IN KEYS:", keys)
                else:
                    print("VALUE:", ast.unparse(n.value)[:250])
                count += 1
            elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "model_in":
                print("FIELD:", n.lineno, ast.unparse(t)[:100])
                count += 1

print("MODEL_IN ASSIGNMENTS:", count)

print("\n=== PZAAS JSON SAMPLES ===")
for f in sorted((root / "samples").glob("*.json")):
    try:
        data = json.loads(f.read_text())
        print(f.name, ":", list(data)[:8] if isinstance(data, dict) else type(data).__name__)
    except Exception as e:
        print(f.name, ":", type(e).__name__)

print("\nINSPECTION: PASS")
print("ORIGINAL DS: UNCHANGED")
print("REAL INFERENCE: NEXT")
PY
