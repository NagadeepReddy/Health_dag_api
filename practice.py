podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'grep -Rn -B 5 -A 10 "_import_custom_architectures()" /opt/venv/lib/python3.12/site-packages/max/pipelines/ | head -65'
