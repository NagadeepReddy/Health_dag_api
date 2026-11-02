ROOT=/application1/sajjna8/rt-pzai-bplan-v1
EXT="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension"

python3 - <<'PY'
from pathlib import Path
import os

ext = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
stage = ext / "bplan_helper_weights_stage/grecbase_aux_weights"
link = ext / "bplan_max_dev/grecbase_aux_weights"

stage.mkdir(parents=True, exist_ok=True)
if link.is_symlink():
    assert link.resolve() == stage.resolve(), "STOP: unexpected existing symlink"
    tmp = link.with_name(link.name + ".relative_tmp")
    assert not tmp.exists() and not tmp.is_symlink()
    tmp.symlink_to(os.path.relpath(stage, link.parent))
    os.replace(tmp, link)
elif not link.exists():
    link.symlink_to(os.path.relpath(stage, link.parent))
else:
    assert link.is_dir(), "STOP: unexpected weight path"

print("BPLAN AUX WEIGHT DIRECTORY: READY", flush=True)
PY

if [ $? -eq 0 ]; then
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT:/workspace:ro" \
  -v "$EXT/bplan_helper_weights_stage/grecbase_aux_weights:/export:rw" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.113-max/maxserve_bplan_extension \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

base = Path("/workspace/artifacts/v1.113/core-artifact/base_model.pt")
state = torch.load(base, map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

prefixes = ("task_embedding.", "ihq_", "jet_", "task_")
weights = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if isinstance(v, torch.Tensor) and k.startswith(prefixes)
}

required = "task_embedding.0.weight"
assert required in weights, f"STOP: {required} absent from checkpoint"

for name, values in weights.items():
    target = Path("/export") / (name + ".npy")
    if target.exists():
        assert np.array_equal(np.load(target), values), \
            f"STOP: differing weight: {name}"
    else:
        with target.open("xb") as f:
            np.save(f, values)

print("BPLAN AUX WEIGHTS: PASS", len(weights), flush=True)

from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
model = BPlanMAXModel()
assert model.base is not None and model.head is not None

print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
fi
