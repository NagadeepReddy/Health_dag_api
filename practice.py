podman run --rm -i -v "$PWD:/workspace" -w /workspace --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
from pathlib import Path

path = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
assert path.is_file(), f"Checkpoint missing: {path}"

checkpoint = torch.load(path, map_location="cpu", weights_only=True)

if isinstance(checkpoint, dict):
    for key in ("state_dict", "model_state_dict"):
        if key in checkpoint and isinstance(checkpoint[key], dict):
            checkpoint = checkpoint[key]
            break

print("=== ORIGINAL PYTORCH FINAL LAYER ===")
matches = [
    (name, tuple(value.shape))
    for name, value in checkpoint.items()
    if "remove_tasks_dense2.weight" in name
    and hasattr(value, "shape")
]

for name, shape in matches:
    print(name, shape)
    print("EXPECTED FINAL OUTPUT DIM:", shape[0])
    print("MAX OUTPUT DIM: 10819")
    print("DIMENSION MATCH:", shape[0] == 10819)

if not matches:
    print("Final layer not found in checkpoint; do not assume output parity.")

print("READ ONLY — NO FILES MODIFIED")
PY
