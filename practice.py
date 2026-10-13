podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

base = Path("artifacts/v1.168-max/cta_max")
wd = base / "grecbase_integration_weights"

inputs = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)
ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
if "state_dict" in ckpt:
    ckpt = ckpt["state_dict"]

with np.load(base / "real_sanity_pytorch_branches.npz") as refs:
    expected = refs["task"].reshape(1, -1).astype(np.float32)

ids = inputs["task_in"]
assert len(ids) == 2

def build(weights):
    parts = [
        F.embedding(
            ids[i].long(),
            torch.from_numpy(weights[i]).float()
        ).reshape(1, -1).numpy()
        for i in range(2)
    ]
    return np.concatenate(parts, axis=1)

trained = [
    ckpt[f"task_embedding.{i}.weight"].cpu().numpy()
    for i in range(2)
]
exported = [
    np.load(wd / f"task_embedding.{i}.weight.npy")
    for i in range(2)
]

pt = build(trained)
mx = build(exported)

assert pt.shape == mx.shape == expected.shape

def check(name, a, b):
    difference = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print(
        name,
        "MATCH:", bool(np.allclose(a, b, rtol=1e-3, atol=1e-3)),
        "MAX_DIFF:", float(difference.max())
    )

print("=== TASK INTEGRATION ROOT CAUSE ===")
check("CHECKPOINT vs PYTORCH REFERENCE", pt, expected)
check("MAX EXPORT vs CHECKPOINT", mx, pt)
check("MAX EXPORT vs PYTORCH REFERENCE", mx, expected)
print("READ ONLY - NO FILES MODIFIED")
PY
