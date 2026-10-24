cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import inspect
from max.pipelines.lib import PipelineModel
from max.pipelines.architectures.llama3.model import Llama3Model

print("=== REQUIRED MAX MODEL METHODS ===")
for name in sorted(PipelineModel.__abstractmethods__):
    method = getattr(PipelineModel, name)
    print(name, inspect.signature(method))

print("\n=== LLAMA IMPLEMENTATION ===")
for name in sorted(PipelineModel.__abstractmethods__):
    method = getattr(Llama3Model, name, None)
    if method:
        print(name, inspect.signature(method))

print("\nMAX MODEL CONTRACT CHECK COMPLETE")
PY
