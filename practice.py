cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2")

files = {
    "SCHEDULER": base / "cta_native_scheduler.py",
    "ADAPTER": base / "cta_worker_adapter.py",
    "FACTORY": base / "cta_scheduler_factory.py",
}

for name, path in files.items():
    print(f"\n=== {name} ===")
    lines = path.read_text().splitlines()
    tree = ast.parse("\n".join(lines))

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            methods = [
                n for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods = [node]
        else:
            continue

        for fn in methods:
            if fn.name not in (
                "__init__", "run_iteration", "predict",
                "initialize", "create_cta_scheduler"
            ):
                continue

            print(f"\nFUNCTION: {fn.name}")
            for i in range(fn.lineno, fn.end_lineno + 1):
                print(f"{i}: {lines[i-1]}")

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
