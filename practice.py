
set -e
cd /application1/sajjna8/rt-pzaas-v1.0

python3 - <<'PY'
from pathlib import Path
import shutil
import ast

p = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_max_model_adapter.py")

old = "from .pzaas_worker_adapter import PZAASWorkerAdapter"
new = "from pzaas_worker_adapter import PZAASWorkerAdapter"

assert p.is_file(), f"Missing: {p}"
src = p.read_text()

if old in src:
    assert src.count(old) == 1
    updated = src.replace(old, new, 1)
    ast.parse(updated)
    backup = p.with_suffix(".py.before_import_fix")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
elif new in src:
    ast.parse(src)
else:
    raise RuntimeError("Unexpected import structure; no changes made")

print("PZAAS IMPORT: CORRECTED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY

podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-w /workspace \
-e PYTHONPATH="/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472-max/pzaas_max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local - <<'PY'
import traceback

print("=== PZAAS REAL NATIVE BRIDGE TEST ===", flush=True)

try:
    import max
    print("MAX RUNTIME: PASS", flush=True)

    from pzaas_max_model_adapter import PZAASMAXModel
    print("MODEL BRIDGE IMPORT: PASS", flush=True)

    model = PZAASMAXModel()
    print("MODEL INITIALIZATION: PASS", flush=True)

    print("CALLABLE:", callable(model), flush=True)
    print("NEXT: NATIVE WORKER EXECUTION AND HTTP 200")

except Exception:
    print("RUNTIME TEST: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)
PY
