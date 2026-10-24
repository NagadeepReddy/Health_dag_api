cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.scheduler.queues import SchedulerZmqConfigs

print("=== EXACT MAX QUEUE DECODING CONFIG ===", flush=True)

for name in ("request_queue_config", "response_queue_config"):
    attr = getattr(SchedulerZmqConfigs, name, None)
    print(f"\n{name}:", attr, flush=True)
    if isinstance(attr, property):
        print(inspect.getsource(attr.fget), flush=True)

print("\n=== QUEUE CONFIG CLASS ===", flush=True)
print(inspect.getsource(SchedulerZmqConfigs), flush=True)
PY
