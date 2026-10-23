cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  -p 127.0.0.1:8000:8000 \
  -v "$PWD:/workspace:Z" \
  --entrypoint /bin/sh localhost/cta-max-faiss:local \
  -c 'cd /workspace && PYTHONPATH=/workspace/artifacts/v1.168-max python -u artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py --headless --devices cpu --model-path TARGET'
