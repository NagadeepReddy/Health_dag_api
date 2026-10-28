timeout 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -m max.entrypoints.pipelines serve --help
