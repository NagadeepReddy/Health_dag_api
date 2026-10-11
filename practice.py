podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import torch
import numpy as np
from pathlib import Path

ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=False
)
base = Path("artifacts/v1.168-max/cta_max/sequence_weights")
prefix = "sequence_transformer.ptransformer.1.fn."

names = {
    "norm1.g": "fn_norm1_g_layer1.npy",
    "norm2.g": "fn_norm2_g_layer1.npy",
    "fused_attn_ff_proj.weight": "fn_fused_attn_ff_proj_weight_layer1.npy",
    "attn_out.weight": "fn_attn_out_weight_layer1.npy",
    "ff_out.1.weight": "fn_ff_out_1_weight_layer1.npy",
}

for key, filename in names.items():
    actual = np.load(base / filename)
    expected = ckpt[prefix + key].numpy()
    print(key, "MATCH:", np.array_equal(actual, expected),
          "MAX DIFF:", np.max(np.abs(actual - expected)))
PY
