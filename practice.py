
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys
import inspect
sys.path.insert(0, "artifacts/v1.168-max")

from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler
from max.serve.scheduler import load_scheduler

cfg = load_scheduler.__globals__["SchedulerZmqConfigs"]

assert callable(create_cta_scheduler)
assert hasattr(cfg, "model_worker_queues")

params = inspect.signature(CTANativeScheduler).parameters
for name in ("adapter", "request_queue", "response_queue", "cancel_queue"):
    assert name in params

print("CTA SCHEDULER FACTORY IMPORT: PASS")
print("NATIVE WORKER QUEUE API: PASS")
print("SCHEDULER FACTORY CONTRACT: PASS")
print("WORKER REGISTRATION: NOT YET IMPLEMENTED")
'
