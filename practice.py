podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")
real = torch.load(p/"real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)
state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

print("PYTORCH:", torch.__version__)
print("\nREAL INPUT KEYS:")
if isinstance(real, dict):
    for k, v in real.items():
        print(k, tuple(v.shape) if hasattr(v, "shape") else type(v).__name__)
else:
    print(type(real).__name__)

print("\nSEQUENCE PAGE-WIDE CHECKPOINT WEIGHTS:")
for k, v in state.items():
    if "sequence_transformer.page_meta_wide" in k:
        print(k, tuple(v.shape))
PY
