podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'import sys; sys.path.insert(0,"artifacts/v1.168-max/cta_max"); import parallel_transformer_block; print("EXPLICIT RMSNORM MODULE IMPORT SUCCESS")'
