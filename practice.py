podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.serve.api_server import Server; print("SERVER:", inspect.signature(Server)); print("METHODS:", [x for x in dir(Server) if not x.startswith("_")])'
