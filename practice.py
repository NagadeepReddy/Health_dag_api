podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.pipelines import PipelineConfig; print("SOURCE:", inspect.getfile(PipelineConfig)); print("BASES:", [c.__name__ for c in PipelineConfig.__mro__]); print(inspect.getsource(PipelineConfig.__init__))'
