timeout 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=64m,mode=1777 \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_model:/cta_native_model:ro \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -m max.entrypoints.pipelines serve \
  --model-path /cta_native_model \
  --devices cpu \
  --quantization-encoding float32 \
  --pretty-print-config
