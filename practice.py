podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
from pathlib import Path

base = Path("artifacts/v1.168")
maxdir = Path("artifacts/v1.168-max/cta_max")
checkpoint = base / "core-artifact/model_0_base.pt"

state = torch.load(checkpoint, map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

print("=== TRAINED SEQUENCE DENSE KEYS ===")
for key, value in state.items():
    if "seq_dense" in key:
        print(key, tuple(value.shape))

print("\n=== EXISTING EXPORTED SEQUENCE WEIGHTS ===")
folder = maxdir / "sequence_weights"
for path in sorted(folder.glob("*.npy")):
    print(path.name)
PY
