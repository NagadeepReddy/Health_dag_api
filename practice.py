podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
import numpy as np
from pathlib import Path

s = torch.load("artifacts/v1.168/core-artifact/model_0_base.pt",
               map_location="cpu", weights_only=False)
base = Path("artifacts/v1.168-max/cta_max/sequence_weights")
prefix = "sequence_transformer.ptransformer.1.fn."

weights = {
    "norm1.g": ("fn_norm1_g_layer1.npy", (256,)),
    "fused_attn_ff_proj.weight": ("fn_fused_attn_ff_proj_weight_layer1.npy", (3072, 256)),
    "attn_out.weight": ("fn_attn_out_weight_layer1.npy", (256, 512)),
    "ff_out.1.weight": ("fn_ff_out_1_weight_layer1.npy", (256, 1024)),
}

for key, (name, shape) in weights.items():
    assert prefix + key in s
    assert tuple(s[prefix + key].shape) == shape

for key, (name, _) in weights.items():
    path = base / name
    if path.exists():
        print("ALREADY EXISTS:", name)
    else:
        np.save(path, s[prefix + key].detach().numpy().astype(np.float32))
        print("SAVED:", name)

print("BLOCK-1 WEIGHTS READY")
PY
