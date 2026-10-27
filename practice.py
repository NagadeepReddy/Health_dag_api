podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -R -n -m 1 'supported_encodings=' /opt/venv/lib/python3.12/site-packages/max/pipelines/architectures 2>/dev/null | head -15"
