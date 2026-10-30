podman --root /application1/podman/storage --runroot /run/containers/storage exec -i -e PYTHONDONTWRITEBYTECODE=1 a176e284b50a /opt/venv/bin/python -B - <<'PY'
import inspect
from max.serve.scheduler import queues

cls = queues.SchedulerZmqConfigs
source = inspect.getsource(cls).splitlines()

print("=== INSTALLED MAX QUEUE CONTRACT ===")
print("MODULE:", inspect.getfile(cls))
print("SIGNATURE:", inspect.signature(cls))

for i, line in enumerate(source, 1):
    print(f"{i}: {line}")

print("\n=== ZMQ CONFIGURATION ===")
ZmqConfig = getattr(queues, "ZmqConfig", None)
if ZmqConfig is not None:
    print("ZmqConfig:", ZmqConfig)
    print("SIGNATURE:", inspect.signature(ZmqConfig))
else:
    print("ZmqConfig: imported from another module")

print("\nQUEUE SOURCE CAPTURED: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
