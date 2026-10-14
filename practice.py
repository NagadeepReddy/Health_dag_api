cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import torch
from unittest.mock import patch

sys.path.insert(0, "artifacts/v1.168-max")

from cta_max.run_real_sanity_input_adapter import build_real_inputs

data = torch.load(
    "artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

with patch.object(torch, "load",
                  side_effect=RuntimeError("Saved loader unexpectedly called")):
    labels, inputs = build_real_inputs(model_in=data)

assert len(labels) == len(inputs) == 72

print("EXPLICIT INPUT DICTIONARY: PASS")
print("SAVED INPUT FALLBACK BYPASSED: PASS")
print("72 INPUTS: PASS")
print("NO FILES MODIFIED")
PY
