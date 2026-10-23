cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=8g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  f30453065dac \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --help

echo "EXIT CODE: $?"
