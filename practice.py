
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"

python3 - <<'PY'
from pathlib import Path
import hashlib
import shutil

source = Path(
    "artifacts/v1.472-max/validation/"
    "pzaas_forward_schema.json"
)

stage = Path(
    "/application1/sajjna8/"
    "PZAAS_MAX_CLEAN_STAGE_20261106"
)

target = stage / source

if not source.is_file():
    raise SystemExit(
        f"STOP: Original runtime schema missing: {source}"
    )

if not stage.is_dir():
    raise SystemExit("STOP: Clean stage missing")

def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if target.exists():
    if checksum(source) != checksum(target):
        raise SystemExit(
            "STOP: Existing staged schema differs from original"
        )
    print("PZAAS RUNTIME SCHEMA: ALREADY PRESENT")
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print("PZAAS RUNTIME SCHEMA: RESTORED")

if checksum(source) != checksum(target):
    raise SystemExit("STOP: Schema verification failed")

print("SCHEMA SHA256 MATCH: PASS")
print("ORIGINAL DS / WEIGHTS: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$STAGE:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import os
import sys
import traceback

os.environ.setdefault("modelId", "rt-pzaas-v1")
os.environ.setdefault("expThrottleLabel", "T")

print("=== CLEAN PZAAS WORKER VERIFICATION ===", flush=True)

try:
    from pipeline import pipeline as PZAASPipeline

    from pzaas_native_serve_dev.pzaas_max_model_adapter import (
        PZAASMAXModel,
        PZAASNativeWorkerAdapter,
    )

    worker = PZAASNativeWorkerAdapter(
        pipeline_factory=PZAASPipeline,
        max_factory=PZAASMAXModel,
    )

    print("CLEAN WORKER INITIALIZATION: START", flush=True)

    loaded = worker.initialize()

    if getattr(loaded, "_pzaas_real_max", None) is None:
        raise RuntimeError("Trained MAX backend not attached")

    print("CLEAN WORKER INITIALIZATION: PASS")
    print("TRAINED MAX BACKEND: ATTACHED")
    print("PZAAS CLEAN RUNTIME: READY FOR HTTP VALIDATION")
    print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")

except BaseException as exc:
    print("CLEAN WORKER BLOCKED:", repr(exc))
    print("=== ROOT ERROR ===")
    print("\n".join(traceback.format_exc().splitlines()[-35:]))
    sys.exit(1)
PY
SH
