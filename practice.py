cd /application1/sajjna8/rt-pzaas-cta-offers-v1

test -f artifacts/v1.168/core-artifact/pipeline.py && \
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --memory=8g \
  -p 127.0.0.1:18080:8000 \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max/cta_max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u artifacts/v1.168-max/maxserve_cta_extension/cta_native_http_entry.py
