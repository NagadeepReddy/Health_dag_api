
podman run --rm --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker

lines = inspect.getsource(ModelWorker.run).splitlines()
keywords = (
    "request_queue", "response_queue", "engine_queue",
    "request_id", "zmq", "get_paged_manager",
    "scheduler.run_iteration", "pipeline="
)
selected = set()
for i, line in enumerate(lines):
    if any(k in line for k in keywords):
        selected.update(range(max(0, i-2), min(len(lines), i+4)))

print("NATIVE WORKER REQUEST/RESPONSE FLOW:")
for i in sorted(selected):
    print(f"{i+1}: {lines[i]}")
'
