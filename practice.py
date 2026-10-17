
podman run --rm \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/cta_extension:ro" \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import importlib.util
import inspect
from max.interfaces.scheduler import Scheduler

p = "/cta_extension/cta_scheduler.py"
spec = importlib.util.spec_from_file_location("cta_scheduler", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cls = module.CTAScheduler
print("NATIVE MAX SCHEDULER:", issubclass(cls, Scheduler))
print("UNIMPLEMENTED METHODS:", sorted(cls.__abstractmethods__))
print("RUN ITERATION:", inspect.signature(cls.run_iteration))
print("SCHEDULER IMPORT: PASS")
'
