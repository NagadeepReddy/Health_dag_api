python3 - <<'PY'
from pathlib import Path
import numpy as np

roots = [
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1"),
    Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
]

for root in roots:
    print(f"\n=== {root.name} ===")
    if not root.is_dir():
        continue
    for name in ("seq_dense.weight.npy", "seq_dense_weight.npy"):
        for p in root.rglob(name):
            try:
                a = np.load(p, mmap_mode="r")
                print(f"{a.shape} | {p}")
            except Exception as e:
                print(f"ERROR: {p} | {e}")
PY
