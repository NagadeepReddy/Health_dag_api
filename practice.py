podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  verizon/modular/max-full:latest python3 - <<'PY'
import torch
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168")
maxdir = Path("artifacts/v1.168-max/cta_max")
state = torch.load(
    base / "core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)
state = state.get("state_dict", state)

checks = {
    "seq_dense.weight": maxdir/"sequence_weights/seq_dense.weight.npy",
    "seq_dense.bias": maxdir/"sequence_weights/seq_dense.bias.npy",
    "sequence_transformer.seq_dense.weight": maxdir/"sequence_weights/seq_dense.weight.npy",
    "sequence_transformer.seq_dense.bias": maxdir/"sequence_weights/seq_dense.bias.npy",
}

for key, path in checks.items():
    print("\nCHECK:", key)
    if key not in state:
        print("Checkpoint key missing")
        continue
    if not path.exists():
        print("Export missing")
        continue
    pt = state[key].detach().cpu().numpy()
    mx = np.load(path, allow_pickle=False)
    print("Shapes:", pt.shape, mx.shape)
    print("Exact match:", np.array_equal(pt, mx))
    if pt.shape == mx.shape:
        print("Max difference:", float(np.max(np.abs(pt-mx))))
PY
