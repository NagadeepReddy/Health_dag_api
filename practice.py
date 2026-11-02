REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
from pathlib import Path
import torch

root = Path("artifacts/v1.113")
checkpoint = torch.load(
    root / "core-artifact/bplan_model.pt",
    map_location="cpu",
    weights_only=True
)

if "state_dict" in checkpoint:
    checkpoint = checkpoint["state_dict"]

print("=== BPLAN TRAINED PREDICTION HEAD ===")
matches = [
    (name, value)
    for name, value in checkpoint.items()
    if isinstance(value, torch.Tensor)
    and (name == "dense1.weight" or name.endswith(".dense1.weight"))
]

for name, weight in matches:
    print("WEIGHT:", name)
    print("SHAPE:", tuple(weight.shape))
    print("DTYPE:", weight.dtype)

assert len(matches) == 1, "STOP: prediction head not uniquely identified"
assert tuple(matches[0][1].shape) == (10438, 2048), \
    "STOP: unexpected trained head dimensions"

print("BPLAN TRAINED PREDICTION HEAD: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
