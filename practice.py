cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.api_server import TokenGeneratorPipeline

print("MAX PIPELINE QUEUE INITIALIZATION")
print("Constructor:", inspect.signature(TokenGeneratorPipeline))

for name in ("__init__", "__aenter__", "__aexit__"):
    method = getattr(TokenGeneratorPipeline, name, None)
    if method:
        print(f"\n=== {name} ===")
        try:
            source = inspect.getsource(method)
            for i, line in enumerate(source.splitlines(), 1):
                print(f"{i}: {line}")
        except (OSError, TypeError):
            print(inspect.signature(method))

print("\nCHECK COMPLETE")
PY
