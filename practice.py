podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import torch

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
lines = p.read_text().splitlines()

print("===== ORIGINAL DENSE2 DEFINITION =====")
for i, line in enumerate(lines):
    if "self.remove_tasks_dense2 =" in line:
        for j in range(i, min(i + 6, len(lines))):
            print(f"{j+1}: {lines[j]}")

print("\n===== CHECKPOINT DENSE2 PARAMETERS =====")
ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)

def inspect(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            name = prefix + str(key)
            if isinstance(value, dict):
                inspect(value, name + ".")
            elif "remove_tasks_dense2" in name:
                print(name, tuple(value.shape) if hasattr(value, "shape") else type(value))

inspect(ckpt)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
