podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from max.pipelines.lib import PIPELINE_REGISTRY; from dataclasses import fields; from max.pipelines.lib import SupportedArchitecture; print("REQUIRED FIELDS:"); [print(f.name, f.type) for f in fields(SupportedArchitecture)]'
