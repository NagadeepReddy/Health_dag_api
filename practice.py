podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'grep -nE "validate|resolve|PipelineConfig|model_config" /opt/venv/lib/python3.12/site-packages/max/entrypoints/pipelines.py | head -45'
