
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path.cwd()
mx = root / "artifacts/v1.472-max"
base = mx / "maxserve_pzaas_extension"
native = base / "pzaas_native_serve_dev"
graph = mx / "pzaas_max/grecbase_fusion_full_head_72_max.py"

print("=== PZAAS REAL MAX NATIVE WORKER CONNECTION ===")

required = {
    "MAX graph": graph,
    "Native worker": native / "pzaas_worker_adapter.py",
    "Native launcher": native / "pzaas_native_launcher.py",
    "Native router": native / "pzaas_router.py",
    "Native HTTP pipeline": native / "pzaas_http_pipeline.py",
}

for name, path in required.items():
    print(f"{name}: {'FOUND' if path.is_file() else 'MISSING'}")

print("\n=== REAL MODULE RESOLUTION ===")

for name, path in {
    "pzaas_max": mx / "pzaas_max",
    "pzaas_max_model_adapter": mx / "pzaas_max_model_adapter.py",
    "native package": native,
}.items():
    print(f"{name}: {'FOUND' if path.exists() else 'NOT FOUND'}")

print("\n=== WORKER ADAPTER CONTRACT ===")

worker = required["Native worker"]

if worker.is_file():
    lines = worker.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if (
            i <= 30
            or 65 <= i <= 115
            or any(k in line for k in (
                "def predict",
                "def initialize",
                "real_max_batch2_backend",
                "attach_max",
                "model_adapter",
            ))
        ):
            print(f"{i}: {line}")

print("\n=== VERIFIED MAX GRAPH ENTRY POINT ===")

if graph.is_file():
    source = graph.read_text()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            print(type(node).__name__, node.name)

    expected = "build_grecbase_fusion_graph_order_correct"
    names = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    print("EXPECTED BUILDER:", "FOUND" if expected in names else "NOT FOUND")

print("\n=== EXISTING PZAAS INPUT AND INFERENCE CODE ===")

for path in sorted(mx.rglob("*.py")):
    if "_cta_native_reference" in str(path):
        continue
    if "pzaas_native_serve_dev" in str(path):
        continue

    name = path.name.lower()
    if not any(x in name for x in (
        "adapter", "backend", "infer", "execute", "parity", "bridge"
    )):
        continue

    print("FILE:", path.relative_to(root))
    try:
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if any(x in node.name.lower() for x in (
                    "infer", "execute", "predict", "attach",
                    "pack", "build", "compile", "forward"
                )):
                    print("  ENTRY:", node.name)
    except (SyntaxError, UnicodeError) as exc:
        print("  INSPECTION ERROR:", str(exc)[:120])

print("\n=== NATIVE BACKEND REFERENCES ===")

for path in sorted(native.glob("*.py")):
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if any(s in line for s in (
            "real_max_batch2_backend",
            "pzaas_max_model_adapter",
            "pzaas_max.",
            "attach_max",
            "predict_raw",
            "/v2/pzaas",
        )):
            print(f"{path.name}:{i}: {line.strip()[:160]}")

print("\n=== PROGRESS ===")
print("LAYER-0 PARITY: PREVIOUSLY PASS")
print("EIGHT-BRANCH PARITY: PREVIOUSLY 8/8 PASS")
print("FULL MODEL PARITY: PREVIOUSLY PASS")
print("NATIVE SCAFFOLD: PREPARED")
print("NATIVE HTTP: NOT VERIFIED")
print("SOURCE FILES MODIFIED: NONE")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: WIRE VERIFIED PZAAS MAX EXECUTOR INTO NATIVE WORKER")
PY
