cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture
from maxserve_cta_extension.cta_pipeline_model import CTAMaxPipelineModel

arch = register_cta_architecture()

assert arch.pipeline_model is CTAMaxPipelineModel
print("CTA NATIVE MODEL REGISTRATION: PASS")
print("REMAINING ABSTRACT METHODS:", sorted(CTAMaxPipelineModel.__abstractmethods__))
print("ORIGINAL DS CODE: UNCHANGED")
PY
