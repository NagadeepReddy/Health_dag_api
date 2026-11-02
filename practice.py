ROOT=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=host \
  -v "$ROOT:/workspace:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension:/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -m bplan_native_serve_dev.bplan_native_launcher
