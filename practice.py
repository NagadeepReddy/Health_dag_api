
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

export PZAAS_STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"

python3 - <<'PY'
import ast
import json
import os
import shutil
import subprocess
from pathlib import Path

repo = Path.cwd()
stage = Path(os.environ["PZAAS_STAGE"])
vendor = repo / "artifacts/v1.472-max/pzaas_max/validation/python_deps"
shared = Path("/application1/max_shared_python_deps")

for path in (stage, vendor, shared):
    if not path.is_dir():
        raise SystemExit(f"STOP: Required directory missing: {path}")

candidates = {}

for path in vendor.iterdir():
    if path.is_dir() and (path / "__init__.py").is_file():
        candidates[path.name] = path
    elif path.is_file() and path.suffix == ".py":
        if path.name != "__init__.py":
            candidates[path.stem] = path

imports = set()
source_roots = [
    repo / "artifacts/v1.472",
    repo / "artifacts/v1.472-max/pzaas_max",
    repo / "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev"
]

for source_root in source_roots:
    for file in source_root.rglob("*.py"):
        if any(part in {
            "__pycache__", "tests", "test",
            "benchmarks", ".pytest_cache"
        } for part in file.parts):
            continue

        try:
            tree = ast.parse(file.read_text(errors="replace"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

needed = sorted(set(candidates) & imports)

print("=== PZAAS VENDORED DEPENDENCY CHECK ===")
print("REFERENCED PACKAGES:", needed, flush=True)

if "einops" not in needed:
    raise SystemExit(
        "STOP: Expected einops dependency not identified"
    )

pythonpath = ":".join([
    "/shared_deps/sklearn161",
    "/shared_deps",
    "/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps",
    "/workspace/artifacts/v1.472-max/maxserve_pzaas_extension",
    "/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev",
    "/workspace/artifacts/v1.472-max",
    "/workspace/artifacts/v1.472/core-artifact",
    "/workspace/artifacts/v1.472/utils/dependency-utils"
])

root_cmd = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
    "run", "--rm", "-i", "--pull=never",
    "--network=none",
    "-v", f"{stage}:/workspace:ro",
    "-v", f"{shared}:/shared_deps:ro",
    "-w", "/workspace",
    "-e", f"PYTHONPATH={pythonpath}",
    "--entrypoint", "/opt/venv/bin/python",
    "localhost/cta-max-faiss:local"
]

probe = """
import importlib.util, json, sys
missing = []
for name in sys.argv[1:]:
    try:
        found = importlib.util.find_spec(name)
    except (ImportError, ValueError, AttributeError):
        found = None
    if found is None:
        missing.append(name)
print(json.dumps(missing))
"""

result = subprocess.run(
    root_cmd + ["-c", probe] + needed,
    text=True, capture_output=True,
    timeout=90
)

if result.returncode:
    raise SystemExit(
        "STOP: Clean dependency probe failed:\n"
        + result.stderr[-1500:]
    )

missing = json.loads(result.stdout.strip().splitlines()[-1])
print("MISSING FROM CLEAN RUNTIME:", missing, flush=True)

for name in missing:
    source = candidates[name]
    destination = shared / source.name

    if destination.exists():
        raise SystemExit(
            f"STOP: Existing shared path conflict: {destination}"
        )

    if source.is_dir():
        shutil.copytree(
            source, destination,
            ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", "*.pyo",
                "tests", ".pytest_cache"
            )
        )
    else:
        shutil.copy2(source, destination)

    print("ADDED TO SHARED RUNTIME:", name, flush=True)

print("SHARED RUNTIME REPAIR: COMPLETE")
print("ORIGINAL DS / MODEL / IMAGE: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PZAAS_STAGE:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PYTEST'
import os
import traceback
import sys

os.environ.setdefault("modelId", "rt-pzaas-v1")
os.environ.setdefault("expThrottleLabel", "T")

try:
    import einops
    print("EINOPS IMPORT: PASS", flush=True)

    from pipeline import pipeline as PZAASPipeline
    print("ORIGINAL PIPELINE IMPORT: PASS", flush=True)

    from pzaas_native_serve_dev.pzaas_max_model_adapter import (
        PZAASMAXModel,
        PZAASNativeWorkerAdapter
    )

    print("CLEAN WORKER: INITIALIZING", flush=True)

    worker = PZAASNativeWorkerAdapter(
        pipeline_factory=PZAASPipeline,
        max_factory=PZAASMAXModel
    )

    loaded = worker.initialize()

    if not hasattr(loaded, "_pzaas_real_max"):
        raise RuntimeError("Trained MAX backend not attached")

    print("CLEAN WORKER INITIALIZATION: PASS")
    print("TRAINED MAX BACKEND: ATTACHED")
    print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")

except BaseException as exc:
    print("CLEAN WORKER BLOCKED:", repr(exc))
    print("\n".join(traceback.format_exc().splitlines()[-30:]))
    sys.exit(1)
PYTEST
SH
