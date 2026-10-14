python3 - <<'PY'
import numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")

for label, filename in [
    ("PYTORCH", "real_sanity_pytorch_same_input_verified.npz"),
    ("MAX", "real_sanity_max_branches.npz"),
]:
    with np.load(b / filename, allow_pickle=False) as f:
        x = f["sibling"].reshape(-1).astype(np.float64)

    mean, maximum = x[:128], x[128:]
    print(f"\n=== {label} ===")
    print("Mean max-abs:", np.max(np.abs(mean)))
    print("Max max-abs:", np.max(np.abs(maximum)))
    print("Mean vs 10 x Max difference:",
          np.max(np.abs(mean - 10 * maximum)))
    print("Mean vs Max difference:",
          np.max(np.abs(mean - maximum)))
PY
