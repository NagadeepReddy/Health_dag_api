
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"

test -d "$STAGE" || {
  echo "STOP: Clean PZAAS stage missing"
  exit 1
}

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

print("=== CLEAN PZAAS DIRECT WORKER DIAGNOSIS ===", flush=True)

try:
    from pipeline import pipeline as PZAASPipeline
    print("ORIGINAL PIPELINE IMPORT: PASS", flush=True)

    from pzaas_native_serve_dev.pzaas_max_model_adapter import (
        PZAASMAXModel,
        PZAASNativeWorkerAdapter,
    )
    print("NATIVE MAX ADAPTER IMPORT: PASS", flush=True)

    worker = PZAASNativeWorkerAdapter(
        pipeline_factory=PZAASPipeline,
        max_factory=PZAASMAXModel,
    )

    print("CLEAN WORKER INITIALIZATION: START", flush=True)

    loaded = worker.initialize()

    print("CLEAN WORKER INITIALIZATION: PASS", flush=True)
    print("PIPELINE TYPE:", type(loaded).__name__)
    print(
        "TRAINED MAX ATTACHED:",
        hasattr(loaded, "_pzaas_real_max")
    )

except BaseException as exc:
    print("\n=== CLEAN WORKER ROOT ERROR ===", flush=True)
    print("ERROR TYPE:", type(exc).__name__, flush=True)
    print("ERROR MESSAGE:", str(exc), flush=True)
    traceback.print_exc()
    sys.exit(1)

print("\nORIGINAL DS / WEIGHTS / MAX IMAGE: UNCHANGED")
PY
SH
