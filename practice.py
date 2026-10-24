cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.queue import zmq_queue

print("=== MAX QUEUE MESSAGE CONTRACT ===")

for name, obj in vars(zmq_queue).items():
    if inspect.isclass(obj) and (
        "Request" in name or "Reply" in name
    ):
        print(name, obj)

from max.serve.queue import queue as queue_module

for name, obj in vars(queue_module).items():
    if inspect.isclass(obj) and "EngineQueue" in name:
        print("\nENGINE QUEUE:", name)
        for method_name in ("open_channel", "response_worker"):
            method = getattr(obj, method_name, None)
            if method:
                print("\n", method_name)
                print(inspect.getsource(method))

print("\nQUEUE CONTRACT CHECK COMPLETE")
PY
