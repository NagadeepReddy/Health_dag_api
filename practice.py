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
    block0_output = torch.from_numpy(saved["after_block0"].copy())
    max_block1 = saved["after_block1"].copy()

real = torch.load(base + "real_sanity_model_in.pt",
                  map_location="cpu", weights_only=True)

state = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True)
state = state.get("state_dict", state)

prefix = "sequence_transformer.ptransformer.1.fn."
weights = {
    k[len(prefix):]: v
    for k, v in state.items() if k.startswith(prefix)
}
assert weights, "Block 1 weights missing"

block = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=2, ff_mult=4
).eval()

block.load_state_dict(weights, strict=True)
print("BLOCK 1 CHECKPOINT LOAD: PASS")

with torch.no_grad():
    pt_block1 = (
        block0_output + block(block0_output, real["vl_in"])
    ).numpy()

assert pt_block1.shape == max_block1.shape

diff = np.abs(
    pt_block1.astype(np.float64) -
    max_block1.astype(np.float64)
)

print("BLOCK 1 MAX_DIFF:", diff.max())
print("BLOCK 1 MEAN_DIFF:", diff.mean())
print("BLOCK 1 MATCH:", np.allclose(
    pt_block1, max_block1, rtol=1e-3, atol=1e-3
))
PY
