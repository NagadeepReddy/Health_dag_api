
podman run --rm --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker

for name, method in inspect.getmembers(ModelWorker, inspect.isfunction):
    source = inspect.getsource(method)
    lines = source.splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if any(x in line for x in (
            "load_scheduler(",
            "run_iteration(",
            "SchedulerResult",
            "scheduler.run",
            "scheduler_task",
        ))
    ]
    if matches:
        print("\nMETHOD:", name)
        shown = set()
        for i in matches:
            for j in range(max(0, i-5), min(len(lines), i+9)):
                if j not in shown:
                    print(lines[j])
                    shown.add(j)
'
