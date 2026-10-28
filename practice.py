cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=2g --cpus=2 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --tmpfs /tmp:rw,size=256m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=64m,mode=1777 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
  -v "$PWD":/workspace:ro \
  -w /workspace \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -m maxserve_cta_extension.cta_native_launcher \
  serve \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --devices cpu \
  --quantization-encoding float32 \
  --port 8765
