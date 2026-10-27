podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -n -B 12 -A 12 'self._resolve_weight_path()' /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/model_config.py"
