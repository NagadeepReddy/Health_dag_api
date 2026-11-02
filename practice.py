python3 - <<'PY'
import torch
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact")

for name in ("base_model.pt", "bplan_model.pt"):
    path = base / name
    print(f"\n=== {name} ===")
    state = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    matches = [
        (k, tuple(v.shape))
        for k, v in state.items()
        if hasattr(v, "shape") and
        ("norm1" in k.lower() or "att_pooling" in k.lower())
    ]

    for key, shape in matches[:50]:
        print(key, shape)

    print("MATCHES:", len(matches))
PY
