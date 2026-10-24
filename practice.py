podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.pipelines.lib import PipelineModel; [print(n, inspect.signature(getattr(PipelineModel,n))) for n in sorted(PipelineModel.__abstractmethods__)]'
