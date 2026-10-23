timeout -k 5s 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=2g \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'sed -n "240,285p" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/registry.py'

echo "EXIT CODE: $?"
