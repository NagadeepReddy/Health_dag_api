cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve import api_server

app = api_server.fastapi_app

print("=== MAX DIRECT STARTUP REQUIREMENTS ===")

for name in ("Settings", "ServingTokenGeneratorSettings"):
    cls = app.__globals__[name]
    print("\n", name)
    for key, param in inspect.signature(cls).parameters.items():
        if param.default is inspect.Parameter.empty:
            print("REQUIRED:", key, param.annotation)

print("\nHTTP FACTORY:", inspect.signature(app))
print("DIRECT STARTUP REQUIREMENTS: PASS")
PY
