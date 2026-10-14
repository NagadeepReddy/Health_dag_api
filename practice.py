python3 - <<'PY'
import numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
max_file = b / "real_sanity_max_branches.npz"
pt_file = b / "real_sanity_pytorch_same_input_verified.npz"

with np.load(max_file, allow_pickle=False) as m, \
     np.load(pt_file, allow_pickle=False) as p:

    for name in ("sequence", "sibling"):
        print(f"\n=== {name.upper()} ===")
        if name not in m or name not in p:
            print("Missing saved key")
            print("MAX keys:", m.files)
            print("PT keys:", p.files)
            continue

        a = np.asarray(m[name], dtype=np.float64)
        e = np.asarray(p[name], dtype=np.float64)

        print("Shapes:", a.shape, e.shape)
        if a.size != e.size:
            print("SIZE MISMATCH")
            continue

        a, e = a.ravel(), e.ravel()
        d = np.abs(a - e)
        print("Max difference:", d.max())
        print("Mean difference:", d.mean())
        print("Worst 8 indices:")
        for i in np.argsort(d)[-8:][::-1]:
            print(f"  {i}: PT={e[i]:.6f}, MAX={a[i]:.6f}, diff={d[i]:.6f}")
PY
