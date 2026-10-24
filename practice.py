podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.pipelines.lib import SupportedArchitecture; from max.pipelines import PIPELINE_REGISTRY; print("ARCH:", inspect.signature(SupportedArchitecture)); print("REGISTER:", inspect.signature(PIPELINE_REGISTRY.register))'
