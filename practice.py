podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
  -v /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_helper_weights_stage/grecbase_integration_weights:/export:rw \
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
if "state_dict" in state:
    state = state["state_dict"]

for name in ("out_norm1", "out_norm2"):
    key = f"sequence_transformer.{name}.g"
    assert key in state, f"Missing checkpoint tensor: {key}"
    values = state[key].detach().cpu().numpy().astype(np.float32)

    print(key, values.shape, flush=True)
    assert values.shape == (256,), f"Unexpected shape: {key}"

    target = Path("/export") / f"{name}_g.npy"
    if target.exists():
        assert np.array_equal(np.load(target), values), f"Existing weight differs: {target}"
        print("VERIFIED:", target.name, flush=True)
    else:
        with target.open("xb") as f:
            np.save(f, values)
        print("EXPORTED:", target.name, flush=True)

print("BPLAN NORMALIZATION WEIGHTS: PASS", flush=True)

from bplan_max_dev.bplan_max_model_adapter import BPlanMAXModel
model = BPlanMAXModel()

print("BPLAN REAL MAX INITIALIZATION: PASS", flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
