
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path.cwd()
mx = root / "artifacts/v1.472-max"
ext = mx / "maxserve_pzaas_extension"
native = ext / "pzaas_native_serve_dev"

print("=== PZAAS FINAL NATIVE CONTRACT CHECK ===")

targets = [
    ext / "pzaas_pipeline_model.py",
    ext / "pzaas_max_model_adapter.py",
    native / "pzaas_native_worker_adapter.py",
    native / "pzaas_worker_adapter.py",
    native / "pzaas_worker_registration.py",
    mx / "pzaas_max_model_adapter.py",
]

for path in targets:
    print("\nFILE:", path.relative_to(root))
    if not path.is_file():
        print("STATUS: MISSING")
        continue

    print("STATUS: FOUND")
    source = path.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print("CLASS:", node.name)
            for method in node.body:
                if isinstance(
                    method,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    print("  METHOD:", method.name,
                          "LINE:", method.lineno)
        elif isinstance(node, (
            ast.FunctionDef,
            ast.AsyncFunctionDef
        )):
            print("FUNCTION:", node.name,
                  "LINE:", node.lineno)

    if path.name in (
        "pzaas_pipeline_model.py",
        "pzaas_worker_adapter.py",
        "pzaas_native_worker_adapter.py",
        "pzaas_max_model_adapter.py",
    ):
        print("--- IMPLEMENTATION ---")
        for i, line in enumerate(lines[:105], 1):
            print(f"{i}: {line}")

print("\n=== VERIFIED PZAAS MAX GRAPH ===")
graph = mx / "pzaas_max/grecbase_fusion_full_head_72_max.py"
print("GRAPH EXISTS:", graph.is_file())

if graph.is_file():
    tree = ast.parse(graph.read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print("ENTRY:", node.name,
                  "LINE:", node.lineno)

print("\n=== NATIVE IMPORT PATHS ===")
for name, path in {
    "actual MAX package": mx / "pzaas_max",
    "factory's MAX development path": ext / "pzaas_max_dev",
    "native serving package": native,
}.items():
    print(name, "FOUND" if path.is_dir() else "MISSING")

print("\n=== PROGRESS ===")
print("LAYER-0: PASS")
print("EIGHT BRANCHES: 8/8 PASS")
print("FULL MODEL PARITY: PASS")
print("MAX CPU: PASS")
print("NATIVE SCAFFOLD: PREPARED")
print("FACTORY / WORKER CONTRACT: PENDING")
print("NATIVE HTTP: NOT VERIFIED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
print("NEXT: REPAIR PZAAS NATIVE FACTORY AND WORKER WIRING")
PY
