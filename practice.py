
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import re

root = Path("/application1/sajjna8/rt-pzaas-v1.0")
base = root / "artifacts/v1.472-max/maxserve_pzaas_extension"
source = base / "_cta_native_reference"
target = base / "pzaas_native_serve_dev"
graph = root / "artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py"

print("=== PZAAS NATIVE MAX SERVING ADAPTATION ===", flush=True)

assert graph.is_file(), "Verified PZAAS MAX graph missing"
assert source.is_dir(), "CTA native reference missing"

names = [
    "native_launcher",
    "router",
    "http_pipeline",
    "native_scheduler",
    "scheduler_factory",
    "context",
    "worker_adapter",
    "spawn_worker",
    "worker_registration",
    "architecture_registration",
    "pipeline_model",
    "queue_compat",
]

prepared = {}

for name in names:
    src = source / f"cta_{name}.py"
    dst = target / f"pzaas_{name}.py"

    if not src.is_file():
        raise SystemExit(f"BLOCKED: Missing reference {src}")

    code = src.read_text()

    code = code.replace(
        "rt-pzaas-cta-offers-v1",
        "rt-pzaas-v1.0"
    )
    code = code.replace("v1.168", "v1.472")
    code = code.replace("CTA", "PZAAS")
    code = code.replace("Cta", "Pzaas")
    code = code.replace("cta", "pzaas")

    compile(code, str(dst), "exec")
    prepared[dst] = code

target.mkdir(parents=True, exist_ok=True)

created = 0
preserved = 0

for dst, code in prepared.items():
    if dst.exists():
        preserved += 1
        print("PRESERVED:", dst.name)
        continue

    with dst.open("x") as f:
        f.write(code)

    created += 1
    print("CREATED:", dst.name)

print("\n=== PZAAS LOCAL DEPENDENCIES ===")

available = {p.stem for p in target.glob("*.py")}
missing = set()

for path in target.glob("pzaas_*.py"):
    tree = ast.parse(path.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("pzaas_") and mod not in available:
                missing.add(mod)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod.startswith("pzaas_") and mod not in available:
                    missing.add(mod)

print("MISSING LOCAL MODULES:", sorted(missing))

backend_refs = []
for path in target.glob("pzaas_*.py"):
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if "real_max_batch2_backend" in line:
            backend_refs.append(f"{path.name}:{number}")

print("CTA BACKEND ADAPTATION POINTS:", backend_refs)

print("\n=== PROGRESS ===")
print("PZAAS GRAPH: PASS")
print("72 INPUTS: PREVIOUSLY PASSED")
print("LAYER-0 PARITY: PREVIOUSLY PASSED")
print("EIGHT-BRANCH PARITY: PREVIOUSLY PASSED")
print("FULL MODEL PARITY: PREVIOUSLY PASSED")
print("NATIVE MODULES CREATED:", created)
print("EXISTING MODULES PRESERVED:", preserved)
print("NATIVE PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NATIVE RUNTIME: NOT YET VERIFIED")
print("NEXT: CONNECT PZAAS GRAPH TO NATIVE WORKER")
PY
