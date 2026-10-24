podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'grep -n -B 12 -A 15 "validate_and_resolve_remaining_pipeline_config" /opt/venv/lib/python3.12/site-packages/max/entrypoints/pipelines.py'
