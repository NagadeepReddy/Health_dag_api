podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c "grep -Rn -B 5 -A 8 'validate_and_resolve_remaining_pipeline_config' /opt/venv/lib/python3.12/site-packages/max/entrypoints/pipelines --include='*.py' 2>/dev/null | head -65"
