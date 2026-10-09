podman run --rm \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'from max.graph import ops; print([x for x in dir(ops) if x in ("where","select","maximum","relu","leaky_relu")])'
