cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from dataclasses import fields
from max.pipelines.architectures.llama3.arch import llama_arch
from max.pipelines.lib import PIPELINE_REGISTRY

architecture_type = type(llama_arch)

print("ARCHITECTURE CLASS:", architecture_type)
print("CONSTRUCTOR:", inspect.signature(architecture_type))
print("FIELDS:", [f.name for f in fields(llama_arch)])
print("REGISTRATION:", inspect.signature(PIPELINE_REGISTRY.register))
print("CTA ARCHITECTURE INTERFACE: CHECK COMPLETE")
PY
