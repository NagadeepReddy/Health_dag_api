timeout 20s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=2g \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'sed -n "1300,1350p" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/config.py'
