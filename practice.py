podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import torch
import numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
s = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)
s = s.get("state_dict", s)

for suffix in ("weight", "bias"):
    path = b / "sequence_weights" / f"seq_dense_{suffix}.npy"
    a = np.load(path, allow_pickle=False)
    print(f"\n=== EXPORTED {suffix.upper()} ===")
    print("Export shape:", a.shape)

    for prefix in ("seq_dense", "sequence_transformer.seq_dense"):
        key = f"{prefix}.{suffix}"
        if key not in s:
            print(key, "MISSING")
            continue
        p = s[key].detach().cpu().numpy()
        print(key, "shape:", p.shape)
        if a.shape == p.shape:
            print("EXACT MATCH:", np.array_equal(a, p))
            print("MAX DIFF:", float(np.max(np.abs(a - p))))
PY
