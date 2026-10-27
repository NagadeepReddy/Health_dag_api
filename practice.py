podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sed \
  localhost/cta-max-faiss:local \
  -n '400,470p' \
  /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/config.py
