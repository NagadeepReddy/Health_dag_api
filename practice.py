podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from max.pipelines import PipelineConfig; p=PipelineConfig(); print("CONFIG CREATED:", type(p).__name__); print("MODEL CONFIG:", type(p.model_config).__name__); print("MODEL PATH:", p.model_config.model_path)'
