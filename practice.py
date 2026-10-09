podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c 'import torch,numpy as np,pathlib; s=torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",map_location="cpu"); d=pathlib.Path("artifacts/v1.168-max/cta_max/context_head_weights"); keys=["context_head.num_batch_norm.weight","context_head.num_batch_norm.bias","context_head.num_batch_norm.running_mean","context_head.num_batch_norm.running_var","context_head.wide_dense.weight","context_head.wide_dense.bias","context_head.wide_swiglu.w1.weight","context_head.wide_swiglu.w2.weight","context_head.wide_swiglu.w3.weight"]; [(np.save(d/(k.replace("context_head.","")+".npy"),s[k].cpu().numpy())) for k in keys]; print("CONTEXTHEAD WIDE REAL WEIGHTS EXPORTED")'
