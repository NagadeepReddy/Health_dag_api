cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472")
p = root / "core-artifact/pipeline.py"
tree = ast.parse(p.read_text())

print("=== ACTUAL DEPENDENCY FILES ===")
for f in sorted(Path("artifacts").rglob("*")):
    if f.is_file() and (
        "requirements" in f.name.lower()
        or f.name.lower().startswith("dockerfile")
    ):
        print(f)
        if "requirements" in f.name.lower():
            for line in f.read_text(errors="replace").splitlines():
                if "apscheduler" in line.lower():
                    print("  DEPENDENCY:", line)

print("\n=== SCHEDULER INVOCATIONS ===")
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        if "schedule_pull" in name or "BackgroundScheduler" in name:
            print("LINE:", node.lineno, name)

print("\n=== DS INITIALIZATION IMPORTS ===")
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        if any(x in node.module for x in (
            "apscheduler", "faiss", "transformers"
        )):
            print("IMPORT:", node.module)

print("RUNTIME INSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
PY
