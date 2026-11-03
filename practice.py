cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import sys

p = Path("artifacts/v1.472/core-artifact/model_0_base.pt")
try:
    import torch
except ImportError:
    sys.exit("PyTorch unavailable on host; container inspection needed")

try:
    state = torch.load(
        p,
        map_location="meta",
        weights_only=True,
        mmap=True
    )
except Exception as e:
    sys.exit(f"METADATA LOAD FAILED: {type(e).__name__}: {e}")

if isinstance(state, dict) and isinstance(state.get("state_dict"), dict):
    state = state["state_dict"]

print("=== PZAAS TRAINED WEIGHT SHAPES ===")
print("Total entries:", len(state))
for k, v in state.items():
    if hasattr(v, "shape") and any(
        x in k.lower() for x in ("seq", "dense", "nlp", "sibling", "task")
    ):
        print(k, tuple(v.shape))

print("PZAAS METADATA INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
PY
