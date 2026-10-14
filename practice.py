podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
folder = base / "sibling_context_weights"

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

print("=== SIBLING WEIGHT AUDIT ===")
matched = missing = mismatched = 0

for path in sorted(folder.glob("*.npy")):
    key = path.stem
    if key not in state:
        print("CHECKPOINT KEY MISSING:", key)
        missing += 1
        continue

    actual = np.load(path, allow_pickle=False)
    expected = state[key].detach().cpu().numpy()

    if actual.shape != expected.shape:
        print("SHAPE MISMATCH:", key, actual.shape, expected.shape)
        mismatched += 1
    elif not np.array_equal(actual, expected):
        print("VALUE MISMATCH:", key,
              float(np.max(np.abs(actual - expected))))
        mismatched += 1
    else:
        matched += 1

print("EXACT MATCH:", matched)
print("MISSING KEYS:", missing)
print("MISMATCHED:", mismatched)
PY
