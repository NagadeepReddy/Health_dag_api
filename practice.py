cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m max.entrypoints.pipelines serve --help 2>&1 |
  grep -i -C 3 -E 'worker.*timeout|timeout.*worker|heartbeat|startup'
