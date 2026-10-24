podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c "sed -n '460,490p;545,565p;1000,1025p' /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/config.py"
