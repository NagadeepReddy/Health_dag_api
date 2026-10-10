podman run --rm \
-v "$PWD:/workspace" \
-w /workspace \
--entrypoint python \
docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
-c '
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

B = Path("artifacts/v1.168-max/cta_max")
W = B / "sequence_weights"

fused = torch.from_numpy(
    np.load(B / "transformer_fused_pytorch.npy")
).float()

ff = fused[..., 1024:]

g = torch.from_numpy(
    np.load(W / "fn_norm2_g.npy")
).float()

norm2 = F.normalize(ff, dim=-1) * (ff.shape[-1] ** 0.5) * g

x, gate = norm2.chunk(2, dim=-1)
swiglu = F.silu(gate) * x

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
'
