cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=host --memory=8g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local \
  -c 'timeout 45s /opt/venv/bin/python \
    -m maxserve_cta_extension.cta_native_launcher \
    --model-path /workspace/artifacts/v1.168/config \
    --port 8000 2>&1' | tail -50
