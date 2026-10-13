cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

b = Path("artifacts/v1.168-max/cta_max")
w = b / "get_path_weights"

def weight(name):
    return torch.from_numpy(
        np.load(w / (name + ".npy")).astype(np.float32)
    )

pt_fusion = torch.from_numpy(
    np.load(b / "real_sanity_pytorch_same_input_verified.npz")["final"].astype(np.float32)
)
max_head = torch.from_numpy(
    np.load(b / "real_sanity_max_get_path_2048_latest.npy").astype(np.float32)
)

with torch.no_grad():
    x = F.linear(
        pt_fusion,
        weight("remove_tasks_dense1.weight"),
        weight("remove_tasks_dense1.bias")
    )
    a = F.linear(x, weight("remove_tasks_act1.w1.weight"))
    c = F.linear(x, weight("remove_tasks_act1.w3.weight"))
    pt_head = F.linear(
        F.silu(a) * c,
        weight("remove_tasks_act1.w2.weight")
    )

assert pt_head.shape == max_head.shape == (1, 2048)

print("PT FUSION vs MAX HEAD:",
      (pt_fusion - max_head).abs().max().item())
print("PT HEAD vs MAX HEAD:",
      (pt_head - max_head).abs().max().item())
print("HEAD PARITY:",
      bool(torch.allclose(pt_head, max_head, rtol=1e-3, atol=1e-3)))
print("HEAD FINITE:", bool(torch.isfinite(pt_head).all()))
PY
