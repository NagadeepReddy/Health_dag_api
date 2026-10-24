cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.api_server import TokenGeneratorPipeline

EngineQueue = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]

print("ENGINE QUEUE:", EngineQueue.__module__)

for name in ("response_worker", "open_channel"):
    print(f"\n=== {name} ===")
    method = getattr(EngineQueue, name, None)
    print(inspect.getsource(method) if method else "NOT FOUND")

print("\nQUEUE HANDOFF REVIEW COMPLETE")
PY
