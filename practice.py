podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import numpy as np
import torch

base = Path("artifacts/v1.168-max/cta_max")

data = torch.load(
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
    ref = saved["task"].reshape(-1).astype(np.float32)

print("=== TASK REFERENCE INPUT IDENTIFICATION ===")
offset = 0

for i in range(2):
    w = weights[f"task_embedding.{i}.weight"].cpu().numpy()
    dim = w.shape[1]
    chunk = ref[offset:offset + dim]
    offset += dim

    if chunk.size != dim:
        raise SystemExit("STOP: Reference dimension mismatch")

    differences = np.max(
        np.abs(w.astype(np.float64) - chunk.astype(np.float64)),
        axis=1
    )
    closest = int(np.argmin(differences))
    actual = int(data["task_in"][i].reshape(-1)[0])

    print(f"TASK {i}")
    print("  CURRENT REAL INPUT ID:", actual)
    print("  SAVED REFERENCE CLOSEST ID:", closest)
    print("  CLOSEST WEIGHT DIFFERENCE:", float(differences[closest]))
    print("  SAME ID:", actual == closest)

assert offset == ref.size, "Unexpected reference layout"
print("READ ONLY — NOTHING MODIFIED")
PY
