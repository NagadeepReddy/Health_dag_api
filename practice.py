
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e CTA_MAX_NATIVE_BOOTSTRAP=1 \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/maxserve_cta_extension/bootstrap \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys
import inspect
from max.serve.pipelines.model_worker import ModelWorker

assert "sitecustomize" in sys.modules, "Bootstrap not loaded"

real_fn = inspect.unwrap(ModelWorker.run)
hook = real_fn.__globals__.get("load_scheduler")

assert getattr(hook, "_cta_hook", False), "CTA hook not activated"

print("FRESH PYTHON BOOTSTRAP: PASS")
print("CTA WORKER HOOK AUTO-ACTIVATION: PASS")
print("SPAWNED MAX WORKER: NOT YET TESTED")
'
