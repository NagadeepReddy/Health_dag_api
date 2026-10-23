podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'python -c "import inspect; from max.pipelines.lib.registry import SupportedArchitecture; print(inspect.signature(SupportedArchitecture))"'
