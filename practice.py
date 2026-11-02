podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:rw \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

root = Path("/workspace/artifacts")
src = root / "v1.113/core-artifact/base_model.pt"
dst = root / "v1.113-max/maxserve_bplan_extension/bplan_helper_weights_stage/grecbase_integration_weights"
dst.mkdir(parents=True, exist_ok=True)

state = torch.load(src, map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

for layer in (0, 1):
    suffix = "" if layer == 0 else "_layer1"
    for norm in ("norm1", "norm2"):
        key = f"sequence_transformer.ptransformer.{layer}.fn.{norm}.g"
        target = dst / f"fn_{norm}_g{suffix}.npy"
        values = state[key].detach().cpu().numpy().astype(np.float32)
        if target.exists():
            assert np.array_equal(np.load(target), values), target
        else:
            np.save(target, values)
        print("PASS:", target.name, values.shape)

print("BPLAN NORMALIZATION WEIGHTS: READY")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
