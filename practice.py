podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import numpy as np
import torch
import torch.nn.functional as F

wd = "artifacts/v1.168-max/cta_max/context_head_weights"

# Same zero input used by MAX runner
x = torch.zeros((1,127), dtype=torch.float32)

# BatchNorm inference
gamma = torch.from_numpy(np.load(f"{wd}/num_batch_norm.weight.npy")).float()
beta  = torch.from_numpy(np.load(f"{wd}/num_batch_norm.bias.npy")).float()
mean  = torch.from_numpy(np.load(f"{wd}/num_batch_norm.running_mean.npy")).float()
var   = torch.from_numpy(np.load(f"{wd}/num_batch_norm.running_var.npy")).float()

x = (x - mean) / torch.sqrt(var + 1e-5)
x = x * gamma + beta

# Dense
w = torch.from_numpy(np.load(f"{wd}/wide_dense.weight.npy")).float()
b = torch.from_numpy(np.load(f"{wd}/wide_dense.bias.npy")).float()
x = F.linear(x, w, b)
x = F.leaky_relu(x, negative_slope=0.2)

# SwiGLU: w2(silu(w1(x)) * w3(x))
w1 = torch.from_numpy(np.load(f"{wd}/wide_swiglu.w1.weight.npy")).float()
w2 = torch.from_numpy(np.load(f"{wd}/wide_swiglu.w2.weight.npy")).float()
w3 = torch.from_numpy(np.load(f"{wd}/wide_swiglu.w3.weight.npy")).float()

pt = F.linear(F.silu(F.linear(x, w1)) * F.linear(x, w3), w2)

mx = torch.from_numpy(
    np.load("artifacts/v1.168-max/cta_max/context_head_wide_max_output.npy")
).float()

diff = torch.max(torch.abs(pt - mx)).item()

print("PT SHAPE:", tuple(pt.shape))
print("MAX SHAPE:", tuple(mx.shape))
print("MAX DIFF:", diff)
print("MATCH:", torch.allclose(pt, mx, rtol=1e-4, atol=1e-5))
PY
