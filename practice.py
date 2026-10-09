podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'import torch; s=torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",map_location="cpu"); [(print(k,tuple(v.shape),v.dtype)) for k,v in s.items() if k.startswith("context_head.num_batch_norm") or k.startswith("context_head.wide_dense") or k.startswith("context_head.wide_swiglu")]'
