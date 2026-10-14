cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import torch
import numpy as np

sys.path.insert(0, "artifacts/v1.168-max")
sys.path.insert(0, "artifacts/v1.168-max/cta_max")

from cta_max.run_live_max_inference import infer_max_live

data = torch.load(
    "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

result = infer_max_live(data)

assert result.shape == (1, 2048)
assert np.isfinite(result).all()

print("MAX CALLABLE EXECUTION: PASS")
print("OUTPUT SHAPE:", result.shape)
print("NO FILES MODIFIED")
PY
