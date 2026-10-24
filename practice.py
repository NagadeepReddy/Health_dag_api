cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import inspect
from max.serve.api_server import fastapi_app

print("MAX BUILT-IN HTTP APP IMPLEMENTATION:", flush=True)

source = inspect.getsource(fastapi_app)
for n, line in enumerate(source.splitlines(), 1):
    print(f"{n}: {line}")

print("CHECK COMPLETE", flush=True)
PY
