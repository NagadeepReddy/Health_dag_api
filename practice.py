
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys
import inspect
sys.path.insert(0, "artifacts/v1.168-max")

from max.serve.pipelines.model_worker import ModelWorker
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook

fn = ModelWorker.run
real_fn = inspect.unwrap(fn)

print("DIRECT SCHEDULER GLOBAL:", "load_scheduler" in fn.__globals__)
print("UNWRAPPED SCHEDULER GLOBAL:", "load_scheduler" in real_fn.__globals__)

try:
    result = install_cta_scheduler_hook()
    print("CTA HOOK INSTALL:", "PASS" if result else "ALREADY INSTALLED")
    print("CTA HOOK ACTIVE:", getattr(
        real_fn.__globals__.get("load_scheduler"), "_cta_hook", False
    ))
except Exception as exc:
    print("CTA HOOK INSTALL: FAIL")
    print(type(exc).__name__, str(exc))
'
