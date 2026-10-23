podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.serve.pipelines.llm import EngineQueue; print([(n, str(inspect.signature(getattr(EngineQueue,n)))) for n in dir(EngineQueue) if not n.startswith("_") and callable(getattr(EngineQueue,n))])'
