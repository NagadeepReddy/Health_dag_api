python3 - <<'PY'
import numpy as np

b = "artifacts/v1.168-max/cta_max/"

with np.load(b+"real_sanity_max_branches.npz") as f:
    mx = f["sibling"].reshape(-1).copy()

with np.load(b+"real_sanity_pytorch_same_input_verified.npz") as f:
    pt = f["sibling"].reshape(-1).copy()

for name, a, z in [
    ("MEAN DEEP", 0, 64),
    ("MEAN WIDE", 64, 128),
    ("MAX DEEP", 128, 192),
    ("MAX WIDE", 192, 256),
]:
    d = np.abs(mx[a:z].astype(np.float64) -
               pt[a:z].astype(np.float64))
    print(name, "MAX DIFF:", d.max(),
          "MEAN DIFF:", d.mean())
PY
