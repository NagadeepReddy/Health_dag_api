timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=2g \
  --entrypoint /bin/sh localhost/cta-max-faiss:local -c \
  'grep -R -n "class EngineQueue" /opt/venv/lib/python3.12/site-packages/max/'
