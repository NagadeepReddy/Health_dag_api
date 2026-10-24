podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.interfaces.queue import BackgroundQueueDrainer

for name in ("__init__", "start_draining", "retrieve_item"):
    method = getattr(BackgroundQueueDrainer, name)
    print(f"\n=== {name} ===", flush=True)
    print(inspect.getsource(method), flush=True)
PY
