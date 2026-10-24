cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c '
import inspect
from max.pipelines.lib import PipelineModel

print("MAX PIPELINEMODEL CONTRACT")
print("Constructor:", inspect.signature(PipelineModel.__init__))

for name in sorted(PipelineModel.__abstractmethods__):
    method = getattr(PipelineModel, name)
    print(name, inspect.signature(method))
'
