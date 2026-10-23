podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from dataclasses import fields; from max.pipelines.lib.model_config import MAXModelConfig; print([(f.name, str(f.default)) for f in fields(MAXModelConfig) if any(x in f.name for x in ("model", "path", "repo", "architecture"))])'
