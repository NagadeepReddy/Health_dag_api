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

def w(name):
    return state["sequence_transformer." + name].float()

norm1 = RMSNorm(256).eval()
norm2 = RMSNorm(256).eval()
dense = torch.nn.Linear(512, 256).eval()

norm1.load_state_dict({"g": w("out_norm1.g")})
norm2.load_state_dict({"g": w("out_norm2.g")})
dense.load_state_dict({
    "weight": w("seq_dense.weight"),
    "bias": w("seq_dense.bias")
})

with torch.no_grad():
    normalized = norm1(x)
    pooled = torch.cat(
        [normalized.mean(1), normalized.max(1).values], dim=-1
    )
    pt = norm2(dense(pooled)).numpy()

max_final = np.load(base / "real_sanity_max_2048_full_runner.npy")
assert max_final.shape == (1, 2048), max_final.shape
mx = max_final[:, :256]

with np.load(base / "real_sanity_pytorch_same_input_verified.npz") as data:
    reference = data["sequence"].copy()

for label, a, b in [
    ("PYTORCH POSTPROCESS vs MAX", pt, mx),
    ("PYTORCH POSTPROCESS vs SAVED REFERENCE", pt, reference),
    ("MAX vs SAVED REFERENCE", mx, reference)
]:
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print("\n" + label)
    print("MAX_DIFF:", d.max())
    print("MEAN_DIFF:", d.mean())
    print("MATCH:", np.allclose(a, b, rtol=1e-3, atol=1e-3))
PY
