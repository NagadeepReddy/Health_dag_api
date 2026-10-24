cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.pipelines.architectures import SupportedArchitecture
from max.pipelines.lib import PIPELINE_REGISTRY

print("ARCHITECTURE FIELDS:")
print(inspect.signature(SupportedArchitecture))
print("\nREGISTRATION CONTRACT:")
print(inspect.signature(PIPELINE_REGISTRY.register))
print("\nCTA REGISTRATION CONTRACT: READY")
PY
