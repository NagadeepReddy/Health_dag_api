podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_context_head_wide.py
