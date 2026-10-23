podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.entrypoints.cli import serve_api_server_and_model_worker; print(inspect.signature(serve_api_server_and_model_worker))'
