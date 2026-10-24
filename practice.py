cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.api_server import fastapi_app
from max.serve.config import Settings, ServingTokenGeneratorSettings

print("=== REQUIRED DIRECT STARTUP ARGUMENTS ===")

for cls in (Settings, ServingTokenGeneratorSettings):
    print(f"\n{cls.__name__}:")
    for name, p in inspect.signature(cls).parameters.items():
        if p.default is inspect.Parameter.empty:
            print("REQUIRED:", name, p.annotation)

print("\nBUILT-IN HTTP FACTORY:", inspect.signature(fastapi_app))
print("CHECK COMPLETE")
PY
