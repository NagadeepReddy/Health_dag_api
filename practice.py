podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from max.interfaces import PipelineTask; print("MAX TASKS:", [(x.name, x.value) for x in PipelineTask])'
