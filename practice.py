podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact:/source:ro \
  -v /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_helper_weights_stage/grecbase_integration_weights:/export:rw \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

state = torch.load("/source/base_model.pt", map_location="cpu", weights_only=True)
if "state_dict" in state:
    state = state["state_dict"]

for name, shape in [("out_norm1", (256,)), ("out_norm2", (2048,))]:
    key = f"sequence_transformer.{name}.g"
    assert key in state, f"STOP: missing checkpoint tensor {key}"
    values = state[key].detach().cpu().numpy().astype(np.float32)
    assert values.shape == shape, f"STOP: unexpected shape for {key}"

    target = Path("/export") / f"{name}_g.npy"
    if target.exists():
        assert np.array_equal(np.load(target), values), f"STOP: existing weight differs: {target}"
        print("VERIFIED:", target.name, values.shape)
    else:
        with target.open("xb") as f:
            np.save(f, values)
        print("EXPORTED:", target.name, values.shape)

print("BPLAN OUTPUT NORMALIZATION WEIGHTS: READY")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
