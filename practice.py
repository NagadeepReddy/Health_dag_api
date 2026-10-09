cat > artifacts/v1.168-max/cta_max/run_transformer_parity.py <<'PY'
import sys
import torch
import numpy as np

# Original CTA implementation is the source of truth.
sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
from models import ParallelTransformerBlock

CKPT = "artifacts/v1.168/core-artifact/model_0_base.pt"
PREFIX = "sequence_transformer.ptransformer.0.fn."

torch.manual_seed(1234)

# Exact block dimensions already verified from the real CTA model.
pt = ParallelTransformerBlock(
    dim=256,
    dim_head=256,
    heads=2,
    ff_mult=4,
)
pt.eval()

state = torch.load(CKPT, map_location="cpu")
block_state = {
    k[len(PREFIX):]: v
    for k, v in state.items()
    if k.startswith(PREFIX)
}

result = pt.load_state_dict(block_state, strict=True)
print("PYTORCH REAL WEIGHTS:", result)

# Deterministic input to be reused by MAX.
x = torch.randn(1, 4, 256)

# All four positions valid.
vl = torch.tensor([4], dtype=torch.long)

np.save(
    "artifacts/v1.168-max/cta_max/transformer_input.npy",
    x.numpy(),
)

with torch.no_grad():
    y = pt(x, vl=vl)

np.save(
    "artifacts/v1.168-max/cta_max/transformer_pytorch_output.npy",
    y.detach().cpu().numpy(),
)

print("INPUT :", tuple(x.shape))
print("OUTPUT:", tuple(y.shape))
print("PYTORCH TRANSFORMER REFERENCE SAVED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_parity.py
