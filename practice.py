cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none \
  --memory=8g --memory-swap=8g --pids-limit=64 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactory.verizon.com/modular/max-full:latest \
  -u -c 'from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler; print("REAL MAX CTA FACTORY IMPORT: PASS", flush=True)'
