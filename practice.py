cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import inspect
from max.serve import api_server

print("MAX NATIVE SERVER ENTRY POINTS:")
for name, obj in vars(api_server).items():
    if (inspect.isfunction(obj) or inspect.isclass(obj)) and any(
        term in name.lower()
        for term in ("server", "serve", "app", "route")
    ):
        try:
            print(name, inspect.signature(obj))
        except (TypeError, ValueError):
            print(name)
print("CHECK COMPLETE")
PY
