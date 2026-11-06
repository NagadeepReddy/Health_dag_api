
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472-max/maxserve_pzaas_extension")
names = (
    "pzaas_worker_adapter.py",
    "pzaas_pipeline_factory.py",
    "pzaas_native_factory.py",
)

print("=== PZAAS ORIGINAL PIPELINE BASELINE ENTRY POINTS ===")

found = False

for name in names:
    matches = sorted(root.rglob(name))

    for path in matches:
        found = True
        lines = path.read_text().splitlines()
        tree = ast.parse("\n".join(lines), filename=str(path))

        print(f"\nFILE: {path}")

        print("--- Imports ---")
        for line in lines[:28]:
            if line.startswith(("from ", "import ")):
                print(line)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                print(f"\nFUNCTION: {node.name} at line {node.lineno}")
                if node.name in (
                    "create_pipeline", "pipeline_factory",
                    "make_pipeline", "build_pipeline"
                ):
                    for i in range(node.lineno, min(node.end_lineno, node.lineno + 34) + 1):
                        print(f"{i}: {lines[i-1]}")

            elif isinstance(node, ast.ClassDef):
                print(f"\nCLASS: {node.name}")
                for method in node.body:
                    if not isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ):
                        continue

                    print(f"  METHOD: {method.name} line {method.lineno}")

                    if method.name in (
                        "__init__", "predict_raw", "load",
                        "predict", "create", "get_pipeline"
                    ):
                        end = min(method.end_lineno, method.lineno + 28)
                        for i in range(method.lineno, end + 1):
                            print(f"{i}: {lines[i-1]}")

if not found:
    print("NO MATCHING FACTORY / WORKER FILES FOUND")

print("\n=== ORIGINAL DS / MAX FILES: UNCHANGED ===")
PY
