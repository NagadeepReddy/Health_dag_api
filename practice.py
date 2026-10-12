python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
files = [root / "core-artifact/pipeline.py"]
files += sorted(root.rglob("Model.py"))

for path in files:
    if not path.is_file():
        continue

    src = path.read_text()
    lines = src.splitlines()
    tree = ast.parse(src)

    print(f"\n===== {path} =====")

    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        methods = {
            n.name: n for n in cls.body
            if isinstance(n, ast.FunctionDef)
        }

        if not any(name in methods for name in
                   ("preprocess", "predict_raw", "_extract_json")):
            continue

        print("CLASS:", cls.name)

        for name in ("__init__", "preprocess", "predict_raw", "predict"):
            if name in methods:
                n = methods[name]
                print(" METHOD:", name, ast.unparse(n.args)[:200])

        if "__init__" in methods:
            n = methods["__init__"]
            print(" INITIALIZATION:")
            for i in range(n.lineno, min(n.end_lineno, n.lineno + 24) + 1):
                print(f"  {i}: {lines[i-1][:180]}")

    print(" PIPELINE CALL SITES:")
    shown = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            expr = ast.unparse(n.func)
            if any(k in expr for k in
                   ("Pipeline(", "pipeline.predict_raw",
                    "pipeline.preprocess", "self.pipeline")):
                print(" ", n.lineno, ast.unparse(n)[:220])
                shown += 1
                if shown >= 8:
                    break

print("\nREAD ONLY — NO FILES MODIFIED")
PY
