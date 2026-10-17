
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys, inspect
sys.path.insert(0, "artifacts/v1.168-max")

from max.serve.pipelines.model_worker import ModelWorker
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook

real_fn = inspect.unwrap(ModelWorker.run)
original = real_fn.__globals__["load_scheduler"]

assert install_cta_scheduler_hook() is True
hook = real_fn.__globals__["load_scheduler"]
assert getattr(hook, "_cta_hook", False)
assert hook is not original
assert install_cta_scheduler_hook() is False

print("CTA WORKER HOOK INSTALL: PASS")
print("REAL WORKER GLOBAL PATCH: PASS")
print("REPEATED INSTALL PROTECTION: PASS")
print("SPAWNED WORKER ACTIVATION: STILL PENDING")
'
