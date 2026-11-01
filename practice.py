podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --entrypoint python3 \
  localhost/cta-max-faiss:local \
  -c "import importlib.util; print({m: bool(importlib.util.find_spec(m)) for m in ['torch','transformers','faiss','numpy','pandas','max']})"
