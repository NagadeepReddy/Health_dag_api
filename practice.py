podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

root = Path("artifacts/v1.168")
sys.path.insert(0, str(root / "utils/dependency-utils"))
from models import ParallelTransformerBlock

pt = ParallelTransformerBlock(
    dim=256, dim_head=256, heads=1, ff_mult=4
).eval()

state = torch.load(
    root / "core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True, mmap=True
)
if "state_dict" in state:
    state = state["state_dict"]
elif "model_state_dict" in state:
    state = state["model_state_dict"]

weights = {
    k.removeprefix("att_pooling."): v
    for k, v in state.items()
    if k.startswith("att_pooling.")
}
pt.load_state_dict(weights, strict=True)

x = torch.from_numpy(
    np.random.default_rng(42)
    .standard_normal((1, 8, 256))
    .astype(np.float32) * 0.01
)

with torch.inference_mode():
    normalized = pt.norm1(x)
    projected = pt.fused_attn_ff_proj(normalized)
    q, k, v, ff = projected.split(
        [256, 256, 256, 2048], dim=-1
    )

    ff = pt.norm2(ff)
    first, second = ff.chunk(2, dim=-1)

    original = pt.ff_out[0](ff)
    first_gated = F.silu(first) * second
    second_gated = first * F.silu(second)

    print("===== SWIGLU ORDER =====")
    print("FIRST HALF GATED DIFF:",
          (original - first_gated).abs().max().item())
    print("SECOND HALF GATED DIFF:",
          (original - second_gated).abs().max().item())

    print("\n===== ROTARY POSITIONS =====")
    reference_pos = pt.get_rotary_embedding(8, x.device)
    freq = pt.rotary_emb.inv_freq
    angles = torch.outer(
        torch.arange(8, dtype=torch.float32), freq
    )
    max_pos = torch.cat([angles, angles], dim=-1)

    print("PYTORCH ROTARY SHAPE:", tuple(reference_pos.shape))
    print("MAX POSITION SHAPE:", tuple(max_pos.shape))
    print("ROTARY MAX DIFF:",
          (reference_pos - max_pos).abs().max().item())

    print("\n===== PADDING MASK =====")
    mask = pt.create_key_padding_mask(
        seq_in=x, valid_length=None
    )
    print("MASK SHAPE:", tuple(mask.shape))
    print("MASKED POSITIONS:", int(mask.sum().item()))

print("\nDIAGNOSTIC COMPLETE — NO FILES MODIFIED")
PY
