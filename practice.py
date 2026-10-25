cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=4g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -m maxserve_cta_extension.cta_native_launcher \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --custom-architectures /workspace/artifacts/v1.168-max/cta_native_model \
  2>&1 | tail -65
