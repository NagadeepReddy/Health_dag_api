podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.serve import Server; from max.serve.config import Settings; print("SERVER:", inspect.signature(Server)); print("SETTINGS:", inspect.signature(Settings)); print("METHODS:", [x for x in dir(Server) if not x.startswith("_")])'
