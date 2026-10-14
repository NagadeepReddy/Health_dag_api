podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np
import torch
from pathlib import Path

sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
from models import RMSNorm

base = Path("artifacts/v1.168-max/cta_max")

with np.load(base / "max_sequence_stages_diag.npz") as data:
    x = torch.from_numpy(data["after_block1"].copy())

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

def weight(name):
    return state["sequence_transformer." + name].float()

norm1 = RMSNorm(256).eval()
norm2 = RMSNorm(256).eval()
dense = torch.nn.Linear(512, 256).eval()

norm1.load_state_dict({"g": weight("out_norm1.g")})
norm2.load_state_dict({"g": weight("out_norm2.g")})
dense.load_state_dict({
    "weight": weight("seq_dense.weight"),
    "bias": weight("seq_dense.bias")
})

with torch.no_grad():
    x = norm1(x)
    pooled = torch.cat(
        [x.mean(dim=1), x.max(dim=1).values],
        dim=-1
    )
    pt_sequence = norm2(dense(pooled)).numpy()

with np.load(base / "real_sanity_pytorch_same_input_verified.npz") as data:
    expected = data["sequence"]

assert pt_sequence.shape == expected.shape

diff = np.abs(
    pt_sequence.astype(np.float64) -
    expected.astype(np.float64)
)

print("PYTORCH POSTPROCESS MAX_DIFF:", diff.max())
print("PYTORCH POSTPROCESS MEAN_DIFF:", diff.mean())
print("PYTORCH POSTPROCESS MATCH:", np.allclose(
    pt_sequence, expected, rtol=1e-3, atol=1e-3
))
PY
