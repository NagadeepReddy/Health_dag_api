timeout -s TERM -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=4g --cpus=2 --pids-limit=128 \
  --network=none --read-only \
  --log-driver=none \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /root:rw,size=64m \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e HOME=/tmp -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp/cache \
  -e HF_HOME=/tmp/hf \
  -e MODULAR_HOME=/tmp/modular \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model
