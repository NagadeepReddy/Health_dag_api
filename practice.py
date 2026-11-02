ROOT=/application1/sajjna8/rt-pzai-bplan-v1
DEST="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/sibling_context_weights"

mkdir -p "$DEST" && podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$ROOT/artifacts/v1.113/core-artifact:/source:ro" \
  -v "$DEST:/export:rw" \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import torch
import numpy as np
from pathlib import Path

state = torch.load(
    "/source/base_model.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

weights = {
    k: v.detach().cpu().numpy()
    for k, v in state.items()
    if k.startswith("sibling_context_head.") and isinstance(v, torch.Tensor)
}

assert "sibling_context_head.deep_embedding.0.weight" in weights, \
    "STOP: required sibling tensor absent from checkpoint"

count = 0
for name, values in weights.items():
    target = Path("/export") / (name + ".npy")
    if target.exists():
        assert np.array_equal(np.load(target), values), \
            f"STOP: existing weight differs: {name}"
    else:
        with target.open("xb") as f:
            np.save(f, values)
        count += 1

print("BPLAN SIBLING WEIGHTS: READY", flush=True)
print("TOTAL TENSORS:", len(weights), flush=True)
print("NEWLY EXPORTED:", count, flush=True)
print("ORIGINAL DS AND CTA: UNCHANGED", flush=True)
PY
