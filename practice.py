python - <<'PY'
import numpy as np
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")

files = {
    "Verified PyTorch": "real_sanity_pytorch_same_input_verified.npz",
    "Original PyTorch": "real_sanity_pytorch_branches.npz",
    "Saved MAX": "real_sanity_max_branches.npz",
}

arrays = {}
for label, filename in files.items():
    with np.load(p / filename, allow_pickle=False) as data:
        arrays[label] = data["sequence"].copy()

reference = arrays["Verified PyTorch"]

for label, actual in arrays.items():
    diff = np.abs(actual.astype(np.float64) - reference.astype(np.float64))
    print(label)
    print("  MAX_DIFF:", float(diff.max()))
    print("  MEAN_DIFF:", float(diff.mean()))
    print("  MATCH:", bool(np.allclose(actual, reference, rtol=1e-3, atol=1e-3)))
PY
