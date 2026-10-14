python - <<'PY'
import numpy as np
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")

pairs = [
    ("attention", "transformer_attention_pytorch.npy", "transformer_attention_max.npy"),
    ("ff", "transformer_ff_pytorch.npy", "transformer_ff_max.npy"),
    ("norm2", "transformer_exact_norm2.npy", "transformer_exact_norm2.npy"),
]

for label, pt_name, max_name in pairs:
    pt_path, max_path = p / pt_name, p / max_name
    if not pt_path.exists() or not max_path.exists():
        print(label, "SKIP: file missing")
        continue
    a, b = np.load(pt_path), np.load(max_path)
    print(label, "shapes:", a.shape, b.shape)
    if a.shape == b.shape:
        d = np.abs(a.astype(np.float64) - b.astype(np.float64))
        print("  MAX_DIFF:", float(d.max()))
        print("  MEAN_DIFF:", float(d.mean()))
PY
