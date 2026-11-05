
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.472-max/maxserve_pzaas_extension/_cta_native_reference")

files = [
    "cta_native_launcher.py",
    "cta_router.py",
    "cta_worker_adapter.py",
    "cta_pipeline_model.py",
    "cta_http_pipeline.py",
    "cta_architecture_registration.py",
]

print("=== PZAAS NATIVE SERVING INTERFACE MAP ===", flush=True)

for name in files:
    p = base / name
    print(f"\n=== {name} ===")
    if not p.is_file():
        print("MISSING")
        continue

    source = p.read_text()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            line = ast.get_source_segment(source, node)
            print("IMPORT:", line.replace("\n", " ")[:220])

        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            print("DEFINITION:", node.name)

            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        print("  METHOD:", child.name)

    for i, line in enumerate(source.splitlines(), 1):
        if any(token in line.lower() for token in (
            "/v2/cta", "predict_raw", "real_max",
            "cta_worker", "pipeline_model",
            "v1.168", "artifacts/v1.168"
        )):
            print(f"REFERENCE {i}: {line.strip()[:180]}")

print("\nORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: IMPLEMENT PZAAS-SPECIFIC NATIVE SERVING")
PY
