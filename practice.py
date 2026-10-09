podman run --rm \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'from max.graph import ops; names=["arange","concat","cos","sin","reshape","transpose","permute","matmul","softmax","where","broadcast_to","unsqueeze","split","einsum"]; print({n:hasattr(ops,n) for n in names})'
