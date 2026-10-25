cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
-v "$PWD:/workspace:ro" -w /workspace \
-e PYTHONPATH=/workspace/artifacts/v1.168-max \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from max.pipelines.lib import PIPELINE_REGISTRY
from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture

captured = []
original = PIPELINE_REGISTRY.register

def capture(arch, *args, **kwargs):
    captured.append(arch)
    return original(arch, *args, **kwargs)

PIPELINE_REGISTRY.register = capture
register_cta_architecture()

arch = captured[-1]
print("DEFAULT:", arch.default_encoding)
print("SUPPORTED:", list(arch.supported_encodings))
print("FP32 COMPATIBLE:", arch.default_encoding in arch.supported_encodings)
print("TASK:", arch.task)
print("WEIGHTS FORMAT:", arch.default_weights_format)
'
