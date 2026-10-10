python - <<'PY'
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

B = Path("artifacts/v1.168-max/cta_max")
W = B / "sequence_weights"

# Already-proven fused projection output.
fused = torch.from_numpy(
    np.load(B / "transformer_fused_pytorch.npy")
).float()

# FF is the final 2048 values from fused_dims=(512,256,256,2048).
ff = fused[..., 1024:]

# Actual Block-0 norm2 weight.
g = torch.from_numpy(
    np.load(W / "fn_norm2_g.npy")
).float()

# Exact CTA RMSNorm implementation:
# F.normalize(x) * sqrt(dim) * g
norm2 = F.normalize(ff, dim=-1) * (ff.shape[-1] ** 0.5) * g

# Exact CTA SwiGLU implementation:
# x, gate = chunk(2); silu(gate) * x
x, gate = norm2.chunk(2, dim=-1)
swiglu = F.silu(gate) * x

# Actual ff_out Linear weight.
w = torch.from_numpy(
    np.load(W / "fn_ff_out_1_weight.npy")
).float()

ff_out = F.linear(swiglu, w)

np.save(B / "transformer_exact_norm2.npy", norm2.numpy())
np.save(B / "transformer_exact_swiglu.npy", swiglu.numpy())
np.save(B / "transformer_exact_ff_out.npy", ff_out.numpy())

print("FF INPUT :", tuple(ff.shape))
print("NORM2    :", tuple(norm2.shape))
print("SWIGLU   :", tuple(swiglu.shape))
print("FF OUT   :", tuple(ff_out.shape))
print("EXACT FF BOUNDARIES SAVED")
PY
