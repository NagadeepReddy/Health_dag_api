
podman run --rm \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/cta_extension:ro" \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import importlib.util
from max.interfaces.scheduler import Scheduler
from max.serve.scheduler.base import SchedulerProgress

p = "/cta_extension/cta_scheduler.py"
spec = importlib.util.spec_from_file_location("cta_scheduler", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cls = module.CTAScheduler
assert issubclass(cls, Scheduler)
assert not cls.__abstractmethods__
assert module.SchedulerProgress is SchedulerProgress

print("CTA SCHEDULER IMPORT: PASS")
print("NATIVE MAX INTERFACE: PASS")
print("REQUIRED METHODS: PASS")
print("SCHEDULER PROGRESS TYPE: PASS")
'
