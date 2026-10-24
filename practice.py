cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve import api_server

app = api_server.fastapi_app

print("=== BUILT-IN MAX HTTP STARTUP ===")
print("APP:", inspect.signature(app))

for name in ("Settings", "ServingTokenGeneratorSettings"):
    cls = app.__globals__.get(name)
    print("\n", name)
    if cls is None:
        print("NOT FOUND")
        continue
    print("CONSTRUCTOR:", inspect.signature(cls))
    print("MODULE:", cls.__module__)

print("\nDIRECT MAX HTTP STARTUP CONTRACT: CHECK COMPLETE")
PY
