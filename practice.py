cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'python -c "import inspect; from max.pipelines.lib import SupportedArchitecture; print(inspect.signature(SupportedArchitecture))"'
