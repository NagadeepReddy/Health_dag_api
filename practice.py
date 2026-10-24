podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.pipelines.lib import PipelineModel; print("ABSTRACT METHODS:", PipelineModel.__abstractmethods__); print("INIT:", inspect.signature(PipelineModel.__init__))'
