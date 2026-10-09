podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -m py_compile artifacts/v1.168-max/cta_max/parallel_transformer_block.py \
&& echo "TRANSFORMER BLOCK IMPORT/SYNTAX CHECK SUCCESS"
