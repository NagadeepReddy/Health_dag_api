podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.serve.api_server import start_model_worker; print(inspect.signature(start_model_worker)); print(inspect.getsource(start_model_worker)[:5000])'
