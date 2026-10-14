podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import runpy
import numpy as np
import torch
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max").resolve()

# Required paths for the existing runner and its imports
sys.path.insert(0, str(base.parent))
sys.path.insert(0, str(base))

# Run existing MAX implementation, without editing it
result = runpy.run_path(
    str(base / "run_real_sanity_max_branch_diag.py"),
    run_name="__main__"
)

outputs = result["outputs"]
mx = np.asarray(outputs[1].to_numpy(), dtype=np.float32)

# Previously captured Block 1 result
with np.load(base / "max_sequence_stages_diag.npz") as data:
    x = torch.from_numpy(data["after_block1"].copy())

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

sys.path.insert(
    0, "artifacts/v1.168/utils/dependency-utils"
)
from models import RMSNorm

def w(name):
    return state["sequence_transformer." + name].float()

n1 = RMSNorm(256).eval()
n2 = RMSNorm(256).eval()
dense = torch.nn.Linear(512, 256).eval()

n1.load_state_dict({"g": w("out_norm1.g")})
n2.load_state_dict({"g": w("out_norm2.g")})
dense.load_state_dict({
    "weight": w("seq_dense.weight"),
    "bias": w("seq_dense.bias")
})

with torch.no_grad():
    x = n1(x)
    pooled = torch.cat(
        [x.mean(1), x.max(1).values], dim=-1
    )
    pt = n2(dense(pooled)).numpy()

print("\n=== PYTORCH POSTPROCESS vs CURRENT MAX ===")
print("PT SHAPE:", pt.shape)
print("MAX SHAPE:", mx.shape)

assert pt.shape == mx.shape

diff = np.abs(
    pt.astype(np.float64) - mx.astype(np.float64)
)

print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("MATCH:", bool(np.allclose(
    pt, mx, rtol=1e-3, atol=1e-3
)))
print("NOTE: PyTorch uses the previously saved Block 1 tensor.")
PY
