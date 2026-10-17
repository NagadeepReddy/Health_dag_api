
podman run --rm \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import inspect
from max.entrypoints.workers import start_workers
from max.entrypoints.cli import serve_api_server_and_model_worker

for fn in (start_workers, serve_api_server_and_model_worker):
    print("\nFUNCTION:", fn.__name__)
    lines = inspect.getsource(fn).splitlines()
    keywords = ("Process(", "start_method", "spawn", "fork",
                "ModelWorker", "worker.start", "start_workers",
                "model_worker", "pipeline_factory")
    selected = set()
    for i, line in enumerate(lines):
        if any(k in line for k in keywords):
            selected.update(range(max(0, i-3), min(len(lines), i+5)))
    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")
'
