
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v "$PWD:/workspace:ro" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local - <<'PY'
import ast
import importlib.util
from pathlib import Path

print("=== PZAAS NATIVE RUNTIME DEPENDENCY CHECK ===")

files = [
    Path("artifacts/v1.472/core-artifact/pipeline.py"),
    Path("artifacts/v1.472/utils/dependency-utils/models.py"),
]

extension = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension"
)

files.extend(
    sorted(
        (extension / "pzaas_native_serve_dev").glob("*.py")
    )
)

imports = {}

for path in files:
    if not path.is_file():
        print("SOURCE NOT FOUND:", path)
        continue

    tree = ast.parse(path.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [x.name for x in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names = [node.module] if node.module else []
        else:
            continue

        for name in names:
            root = name.split(".")[0]
            imports.setdefault(root, set()).add(path.name)

missing = []

for name in sorted(imports):
    try:
        found = importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        found = False

    if not found:
        missing.append(name)

print("\n=== MISSING IMPORT ROOTS ===")
for name in missing:
    print(name, "| used by:", ", ".join(sorted(imports[name])))

print("\n=== IMPORTANT RUNTIME PACKAGES ===")
for name in [
    "apscheduler", "einops", "torch",
    "transformers", "faiss", "max",
    "sklearn", "pandas", "numpy"
]:
    try:
        ok = importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        ok = False

    print(name, "FOUND" if ok else "MISSING")

print("\n=== PROGRESS ===")
print("MAX CPU: PASS")
print("LAYER-0: PASS")
print("EIGHT BRANCHES: 8/8 PASS")
print("FULL MODEL PARITY: PASS")
print("NATIVE WORKER: DEPENDENCIES PENDING")
print("NATIVE HTTP 200: PENDING")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("NEXT: PACKAGE MISSING REAL DEPENDENCIES TOGETHER")
PY
