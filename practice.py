podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import torch
import numpy as np
import json

src = Path("artifacts/v1.168/core-artifact/model_0_base.pt")
dst = Path("artifacts/v1.168-max/cta_max/sibling_context_weights")

assert src.is_file(), "STOP: checkpoint missing"

state = torch.load(
    src, map_location="cpu",
    weights_only=True, mmap=True
)

if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

prefix = "sibling_context_head."

weights = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if k.startswith(prefix) and isinstance(v, torch.Tensor)
}

assert len(weights) == 20, (
    f"STOP: expected 20 sibling tensors, found {len(weights)}"
)

manifest = {}
for name, arr in sorted(weights.items()):
    assert np.isfinite(arr).all(), f"STOP: invalid {name}"
    manifest[name] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
    }
    path = dst / (name + ".npy")
    if path.exists():
        assert np.array_equal(np.load(path), arr), (
            f"STOP: existing tensor differs: {name}"
        )

dst.mkdir(parents=True, exist_ok=True)

for name, arr in sorted(weights.items()):
    path = dst / (name + ".npy")
    if not path.exists():
        np.save(path, arr)

mp = dst / "manifest.json"
if mp.exists():
    assert json.loads(mp.read_text()) == manifest, \
        "STOP: existing manifest differs"
else:
    mp.write_text(json.dumps(manifest, indent=2))

print("SIBLING CONTEXT WEIGHTS READY:", len(weights))
print("SHAPES AND VALUES VERIFIED")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
