cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.queue.engine_queue import EngineQueue

for name in ("response_worker", "open_channel"):
    method = getattr(EngineQueue, name, None)
    print(f"\n=== {name} ===", flush=True)
    print(inspect.getsource(method) if method else "NOT FOUND")
PY
