
cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=host --memory=4g \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONUNBUFFERED=1 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  > /tmp/cta_native_startup.log 2>&1

rc=$?
echo "STARTUP EXIT CODE: $rc"
tail -65 /tmp/cta_native_startup.log
