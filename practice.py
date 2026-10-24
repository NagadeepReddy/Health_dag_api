cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout 45s podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --model-path /workspace/artifacts/v1.168/config \
  --port 8000 2>&1 | tee /tmp/cta_factory_start.log | tail -35
