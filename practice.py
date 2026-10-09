podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'import importlib.util; from max.graph import ops; p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"; spec=importlib.util.spec_from_file_location("ptb",p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print("MODULE IMPORT SUCCESS"); print([x for x in ["arange","concat","cos","sin","reshape","transpose","permute","matmul","softmax","where","broadcast_to","unsqueeze"] if hasattr(ops,x)])'
