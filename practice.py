
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 180s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=8g \
  -p 127.0.0.1:18080:8000 \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --headless --devices cpu \
  --model-path /workspace/artifacts/v1.168/core-artifact \
  --port 8000
