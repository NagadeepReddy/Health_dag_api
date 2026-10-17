
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys
import inspect
sys.path.insert(0, "artifacts/v1.168-max")

from max.interfaces.scheduler import Scheduler
from max.serve.scheduler.base import SchedulerProgress
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler

assert issubclass(CTANativeScheduler, Scheduler)
assert not inspect.isabstract(CTANativeScheduler)
assert callable(CTANativeScheduler.run_iteration)

params = inspect.signature(CTANativeScheduler.__init__).parameters
for name in ("adapter", "request_queue", "response_queue", "cancel_queue"):
    assert name in params, f"Missing constructor parameter: {name}"

assert hasattr(SchedulerProgress, "MADE_PROGRESS")
assert hasattr(SchedulerProgress, "NO_PROGRESS")

print("CTA NATIVE SCHEDULER IMPORT: PASS")
print("MAX SCHEDULER INTERFACE: PASS")
print("NATIVE QUEUE CONSTRUCTOR: PASS")
print("SCHEDULER PROGRESS CONTRACT: PASS")
'
