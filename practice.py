podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import torch
import torch.nn.functional as F
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")

inputs = torch.load(
    base / "real_sanity_model_in.pt",
    map_location="cpu", weights_only=True
)

weights = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)

if "state_dict" in weights:
    weights = weights["state_dict"]

with np.load(
    base / "real_sanity_pytorch_branches.npz",
    allow_pickle=False
) as saved:
    reference = saved["task"].astype(np.float32).copy()

with torch.no_grad():
    parts = []
    for i in range(2):
        ids = inputs["task_in"][i].long()
        w = weights[f"task_embedding.{i}.weight"].float()
        parts.append(F.embedding(ids, w).reshape(1, -1))

    actual = torch.cat(parts, dim=-1).numpy()

print("=== TASK ORIGINAL MODEL VS SAVED REFERENCE ===")
print("TASK INPUT IDS:", [x.tolist() for x in inputs["task_in"]])
print("COMPUTED SHAPE:", actual.shape)
print("REFERENCE SHAPE:", reference.shape)

if actual.shape != reference.shape:
    raise SystemExit("TASK SHAPE MISMATCH")

diff = np.abs(actual.astype(np.float64) -
              reference.astype(np.float64))

print("MAX DIFFERENCE:", float(diff.max()))
print("MATCH:", bool(np.allclose(
    actual, reference, rtol=1e-3, atol=1e-3
)))
print("NO FILES MODIFIED")
PY
