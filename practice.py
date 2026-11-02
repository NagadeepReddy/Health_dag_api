ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"

python3 - <<'PY'
from pathlib import Path
import os

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
folder = root / "bplan_max_dev/main_context_weights"

if folder.is_symlink():
    resolved = folder.resolve()
    assert resolved.is_dir() and resolved.is_relative_to(root.resolve()), \
        "STOP: unexpected main-context symlink target"
    relative = os.path.relpath(resolved, folder.parent)
    folder.unlink()
    folder.symlink_to(relative)
    print("MAIN CONTEXT SYMLINK: PORTABLE", flush=True)
else:
    folder.mkdir(parents=True, exist_ok=True)

assert folder.is_dir()
print("MAIN CONTEXT DESTINATION: READY", flush=True)
PY

if [ $? -eq 0 ]; then
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -v "$EXT/bplan_max_dev/main_context_weights:/export:rw" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

state = torch.load(
    "/workspace/artifacts/v1.113/core-artifact/base_model.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

weights = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if k.startswith("context_head.") and isinstance(v, torch.Tensor)
}
assert "context_head.deep_embedding.0.weight" in weights

for name, values in weights.items():
    target = Path("/export") / (name + ".npy")
    if target.exists():
        assert np.array_equal(np.load(target), values), \
            f"STOP: differing existing weight: {name}"
    else:
        with target.open("xb") as f:
            np.save(f, values)

print("BPLAN MAIN CONTEXT WEIGHTS: PASS", len(weights), flush=True)

from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
model = BPlanMAXModel()

assert model.base is not None and model.head is not None
print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
fi
