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

# Same 17 categorical inputs used by the MAX test: index 0.
emb = [
    torch.from_numpy(np.load(f"{wd}/deep_embedding_{i}.npy"))[0]
    for i in range(17)
]
x = torch.cat(emb, dim=-1).unsqueeze(0).float()

# Original RMSNorm behavior: weight is checkpoint deep_norm.g.
g = torch.from_numpy(np.load(f"{wd}/deep_norm.g.npy")).float()
eps = 1e-6
x = x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + eps)
x = x * g

# deep_dense
w = torch.from_numpy(np.load(f"{wd}/deep_dense.weight.npy")).float()
b = torch.from_numpy(np.load(f"{wd}/deep_dense.bias.npy")).float()
x = F.linear(x, w, b)

# Original FFSwiGLU: w2(silu(w1(x)) * w3(x))
w1 = torch.from_numpy(np.load(f"{wd}/deep_swiglu.w1.weight.npy")).float()
w2 = torch.from_numpy(np.load(f"{wd}/deep_swiglu.w2.weight.npy")).float()
w3 = torch.from_numpy(np.load(f"{wd}/deep_swiglu.w3.weight.npy")).float()

pt = F.linear(F.silu(F.linear(x, w1)) * F.linear(x, w3), w2)
mx = torch.from_numpy(
    np.load("artifacts/v1.168-max/cta_max/context_head_deep_max_output.npy")
).float()

print("PT SHAPE:", tuple(pt.shape))
print("MAX SHAPE:", tuple(mx.shape))
print("MAX DIFF:", torch.max(torch.abs(pt - mx)).item())
print("MATCH:", torch.allclose(pt, mx, rtol=1e-4, atol=1e-5))
PY
