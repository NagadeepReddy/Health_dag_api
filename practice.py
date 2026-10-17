
podman run --rm \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import inspect
from max.serve.scheduler import load_scheduler
from max.interfaces.scheduler import SchedulerResult

cls = load_scheduler.__globals__["EmbeddingsScheduler"]

print("RESULT CREATION:")
print(inspect.signature(SchedulerResult.create))

print("\nTERMINATED REQUEST HANDLING:")
print(inspect.getsource(cls._handle_terminated_responses))

print("\nQUEUE DRAINER METHODS:")
drainer = cls.__init__.__globals__["BackgroundQueueDrainer"]
for name in ("__init__", "start_draining", "retrieve_item"):
    print(name, inspect.signature(getattr(drainer, name)))
'
