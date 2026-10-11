podman run --rm \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
import numpy as np
from pathlib import Path

s = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=False
)

base = Path("artifacts/v1.168-max/cta_max/sequence_weights")
prefix = "sequence_transformer.ptransformer.1.fn."

weights = {
    "norm1.g": ("fn_norm1_g_layer1.npy", (256,)),
    "fused_attn_ff_proj.weight": ("fn_fused_attn_ff_proj_weight_layer1.npy", (3072, 256)),
    "attn_out.weight": ("fn_attn_out_weight_layer1.npy", (256, 512)),
    "ff_out.1.weight": ("fn_ff_out_1_weight_layer1.npy", (256, 1024)),
}

for key, (name, shape) in weights.items():
    assert prefix + key in s, f"STOP: missing {key}"
    assert tuple(s[prefix + key].shape) == shape, f"STOP: shape mismatch {key}"
    assert not (base / name).exists(), f"STOP: already exists {name}"

for key, (name, _) in weights.items():
    np.save(base / name, s[prefix + key].detach().numpy().astype(np.float32))
    print("SAVED:", name)

print("BLOCK-1 PROJECTION WEIGHTS READY")
PY
