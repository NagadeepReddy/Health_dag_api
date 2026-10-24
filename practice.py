cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:ro" -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper; p=CTAFactoryWrapper(lambda: None)(); print("CTA FACTORY INITIALIZATION PASS:", type(p).__name__)'
