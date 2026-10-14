podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys
import numpy as np
import torch

sys.path.insert(0, "artifacts/v1.168/utils/dependency-utils")
from models import ParallelTransformerBlock

base = "artifacts/v1.168-max/cta_max/"

with np.load(base + "max_sequence_stages_diag.npz") as saved:
    features = torch.from_numpy(saved["features"].copy())
    max_block0 = saved["after_block0"].copy()

real = torch.load(base + "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

prefix = "sequence_transformer.ptransformer.0.fn."
weights = {
    k[len(prefix):]: v
    for k, v in state.items() if k.startswith(prefix)
}

block = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=6, ff_mult=4
).eval()

block.load_state_dict(weights, strict=True)

with torch.no_grad():
    pt_block0 = (
        features + block(features, real["vl_in"])
    ).numpy()

assert pt_block0.shape == max_block0.shape

diff = np.abs(
    pt_block0.astype(np.float64) -
    max_block0.astype(np.float64)
)

print("BLOCK 0 MAX_DIFF:", diff.max())
print("BLOCK 0 MEAN_DIFF:", diff.mean())
print("BLOCK 0 MATCH:", np.allclose(
    pt_block0, max_block0, rtol=1e-3, atol=1e-3
))
PY
