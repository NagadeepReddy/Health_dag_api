cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c "grep -R -n -m 3 'PIPELINE_REGISTRY.register\|register(llama_arch\|def register(self' /opt/venv/lib/python3.12/site-packages/max/pipelines | head -20"
