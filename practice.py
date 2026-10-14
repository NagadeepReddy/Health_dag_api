podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
import numpy as np
from pathlib import Path

root = Path("artifacts/v1.168-max/cta_max")
state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
state = state.get("state_dict", state)

path = root / "grecbase_integration_weights/seq_dense.weight.npy"

print("=== ACTIVE OUTER SEQUENCE WEIGHT ===")
print("Export exists:", path.exists())

if path.exists():
    actual = np.load(path, allow_pickle=False)
    expected = state["seq_dense.weight"].detach().cpu().numpy()
    print("MAX shape:", actual.shape)
    print("PyTorch shape:", expected.shape)
    print("EXACT MATCH:", np.array_equal(actual, expected))
    if actual.shape == expected.shape:
        print("MAX DIFF:", float(np.max(np.abs(actual - expected))))

print("\n=== INTERNAL SEQUENCE WEIGHT ===")
print("Checkpoint shape:",
      tuple(state["sequence_transformer.seq_dense.weight"].shape))
PY
