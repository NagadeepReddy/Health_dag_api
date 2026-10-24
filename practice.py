podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'grep -nE "serve_api_server_and_model_worker|validate_and_resolve|model_factory|start_model_worker" /opt/venv/lib/python3.12/site-packages/max/entrypoints/pipelines.py | head -30'
