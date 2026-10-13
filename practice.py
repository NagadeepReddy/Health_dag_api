podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import torch
import numpy as np

base = Path("artifacts/v1.168-max/cta_max/grecbase_integration_weights")
ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
if "state_dict" in ckpt:
    ckpt = ckpt["state_dict"]

print("=== EXACT WEIGHT MAPPING CHECK ===")

targets = (
    "seq_dense.bias",
    "fused_attn_ff_proj.weight",
)

for target in targets:
    print("\nTARGET:", target)
    for name, value in ckpt.items():
        if target in name:
            arr = value.detach().cpu().numpy()
            print("CHECKPOINT:", name, arr.shape)

    for path in sorted(base.glob("*.npy")):
        if target not in path.name:
            continue
        arr = np.load(path)
        print("EXPORTED:", path.stem, arr.shape)

        candidates = [
            (name, tensor.detach().cpu().numpy())
            for name, tensor in ckpt.items()
            if name.endswith(target) and tensor.shape == arr.shape
        ]
        for name, original in candidates:
            print(
                "  COMPARE:", name,
                "EXACT:", bool(np.array_equal(original, arr)),
                "MAX_DIFF:", float(np.max(
                    np.abs(original.astype(np.float64)
                           - arr.astype(np.float64))
                ))
            )

print("\nREAD ONLY — NO FILES MODIFIED")
PY
