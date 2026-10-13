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
    return torch.from_numpy(np.load(w / (name + ".npy")).astype(np.float32))

fusion = torch.from_numpy(np.load(
    b / "real_sanity_max_2048_verified_latest.npy"
).astype(np.float32))

saved_head = torch.from_numpy(np.load(
    b / "real_sanity_max_get_path_2048_latest.npy"
).astype(np.float32))

with torch.no_grad():
    x = F.linear(fusion,
        weight("remove_tasks_dense1.weight"),
        weight("remove_tasks_dense1.bias"))
    a = F.linear(x, weight("remove_tasks_act1.w1.weight"))
    c = F.linear(x, weight("remove_tasks_act1.w3.weight"))
    expected = F.linear(
        (a * torch.sigmoid(a)) * c,
        weight("remove_tasks_act1.w2.weight"))

assert expected.shape == saved_head.shape == (1, 2048)

print("FUSION vs SAVED HEAD:",
      (fusion - saved_head).abs().max().item())
print("FUSION vs EXPECTED HEAD:",
      (fusion - expected).abs().max().item())
print("SAVED vs EXPECTED HEAD:",
      (saved_head - expected).abs().max().item())
print("EXPECTED HEAD FINITE:",
      bool(torch.isfinite(expected).all()))
PY
