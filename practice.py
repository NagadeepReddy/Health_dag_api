podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'grep -Rn -m 2 "SupportedArchitecture(" /opt/venv/lib/python3.12/site-packages/max/pipelines/architectures/ | head -12'
