podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import numpy as np
import torch

base = Path("artifacts/v1.168-max/cta_max/sequence_weights")
ckpt = torch.load(
    "artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)

required = {
    "seq_dense.weight": (256, 512),
    "seq_dense.bias": (256,),
    "out_norm1.g": (256,),
    "out_norm2.g": (256,),
}

prepared = []
for suffix, shape in required.items():
    key = "sequence_transformer." + suffix
    assert key in ckpt, f"STOP: missing {key}"
    arr = ckpt[key].detach().cpu().numpy()
    assert arr.shape == shape, f"STOP: shape differs for {key}"

    path = base / (suffix.replace(".", "_") + ".npy")
    if path.exists():
        assert np.array_equal(np.load(path), arr), f"STOP: existing file differs: {path}"
        print("ALREADY VERIFIED:", path.name)
    else:
        prepared.append((path, arr))

base.mkdir(parents=True, exist_ok=True)
for path, arr in prepared:
    np.save(path, arr)
    print("SAVED:", path.name)

print("SEQUENCE POSTPROCESS WEIGHTS READY")
print("VERIFIED TRANSFORMER AND DS CODE UNCHANGED")
PY
