cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve import api_server

src = inspect.getsource(api_server.lifespan).splitlines()

print("MAX NATIVE STARTUP FLOW:", flush=True)
for i, line in enumerate(src):
    if any(x in line for x in (
        "start_model_worker",
        "model_factory",
        "pipeline",
        "engine_queue",
        "yield",
    )):
        for j in range(max(0, i - 2), min(len(src), i + 4)):
            print(f"{j+1}: {src[j]}", flush=True)
        print("---", flush=True)

print("CHECK COMPLETE", flush=True)
PY
