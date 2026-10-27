podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -n -C 3 -E 'model_path|config_kwargs|PipelineConfig\(' /opt/venv/lib/python3.12/site-packages/max/entrypoints/pipelines.py | head -85"
