python - <<'PY'
from pathlib import Path
import numpy as np
from datetime import datetime

p = Path("artifacts/v1.168-max/cta_max")
names = [
    "real_sanity_max_branches.npz",
    "real_sanity_max_2048_full_runner.npy",
    "real_sanity_pytorch_same_input_verified.npz",
]

for name in names:
    f = p / name
    print(name, "EXISTS:", f.exists())
    if f.exists():
        print("  MODIFIED:", datetime.fromtimestamp(f.stat().st_mtime))

if not all((p / n).exists() for n in names):
    raise SystemExit("STOP: Required saved output missing")

with np.load(p / names[0]) as z:
    seq = z["sequence"].copy()

final = np.load(p / names[1])

with np.load(p / names[2]) as z:
    ref = z["sequence"].copy()

print("\nSHAPES:", seq.shape, final.shape, ref.shape)

def compare(label, a, b):
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print(label, "MAX_DIFF:", d.max(),
          "MEAN_DIFF:", d.mean(),
          "MATCH:", np.allclose(a, b, rtol=1e-3, atol=1e-3))

compare("MAX SEQUENCE vs VERIFIED PT", seq, ref)

for i in range(8):
    part = final[:, i*256:(i+1)*256]
    compare(f"FINAL SLICE {i} vs MAX SEQUENCE", part, seq)
PY
