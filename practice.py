podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import torch
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "main_context_weights"

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True,
    mmap=True,
)

if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

weights = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if k.startswith("context_head.")
    and isinstance(v, torch.Tensor)
}

assert weights, "STOP: main ContextHead weights not found"
assert sum(".deep_embedding." in k for k in weights) == 17, \
    "STOP: expected 17 main deep embedding tensors"

for name, arr in weights.items():
    assert np.isfinite(arr).all(), f"STOP: invalid {name}"
    path = dst / (name + ".npy")
    if path.exists():
        assert np.array_equal(np.load(path), arr), \
            f"STOP: existing weight differs: {name}"

dst.mkdir(parents=True, exist_ok=True)

for name, arr in sorted(weights.items()):
    path = dst / (name + ".npy")
    if not path.exists():
        np.save(path, arr)

print("MAIN CONTEXT WEIGHTS READY:", len(weights))
print("DEEP EMBEDDINGS: 17")
print("ALL WEIGHTS VERIFIED")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
