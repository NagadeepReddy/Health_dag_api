set -e

ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"
WEIGHTS="$EXT/bplan_helper_weights_stage/grecbase_integration_weights"

test -d "$WEIGHTS" || { echo "STOP: weight directory missing"; exit 1; }

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -v "$WEIGHTS:/export:rw" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

checkpoint = Path("/workspace/artifacts/v1.113/core-artifact/base_model.pt")
state = torch.load(checkpoint, map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

weights = {
    name: tensor.detach().cpu().numpy()
    for name, tensor in state.items()
    if name.startswith("att_pooling.")
    and isinstance(tensor, torch.Tensor)
}

assert "att_pooling.norm2.g" in weights, \
    "STOP: required pooling tensor missing in original checkpoint"

exported = 0

for name, values in weights.items():
    target = Path("/export") / (name + ".npy")

    if target.exists():
        assert np.array_equal(np.load(target), values), \
            f"STOP: existing tensor differs: {name}"
    else:
        with target.open("xb") as file:
            np.save(file, values)
        exported += 1

print("BPLAN POOLING WEIGHTS: PASS", len(weights), flush=True)
print("NEWLY EXPORTED:", exported, flush=True)

from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel

print("BPLAN REAL MAX INITIALIZATION: START", flush=True)
model = BPlanMAXModel()

assert model.base is not None
assert model.head is not None

print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
