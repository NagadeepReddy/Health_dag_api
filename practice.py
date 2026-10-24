cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'grep -RnE "validate_and_resolve|resolve_weight_path|_resolve_weight_path" /opt/venv/lib/python3.12/site-packages/max/pipelines/lib/model_config.py /opt/venv/lib/python3.12/site-packages/max/entrypoints | head -25'
