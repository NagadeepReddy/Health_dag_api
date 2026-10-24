cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.pipelines.lib import PipelineModel
from max.pipelines.architectures.llama3.model import Llama3Model

print("=== REQUIRED MAX MODEL METHODS ===", flush=True)

for name in sorted(PipelineModel.__abstractmethods__):
    print("REQUIRED:", name, inspect.signature(getattr(PipelineModel, name)))
    print("REFERENCE:", inspect.signature(getattr(Llama3Model, name)))

print("MAX MODEL CONTRACT CHECK COMPLETE", flush=True)
PY
