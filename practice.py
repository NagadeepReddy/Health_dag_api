
podman run --rm --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
from max.serve.scheduler import load_scheduler

cls = load_scheduler.__globals__["EmbeddingsScheduler"]
progress = cls.run_iteration.__globals__["SchedulerProgress"]

print("CORRECT IMPORT MODULE:", progress.__module__)
print("SYMBOL:", progress.__name__)
print("MADE_PROGRESS:", progress.MADE_PROGRESS)
print("NO_PROGRESS:", progress.NO_PROGRESS)
'
