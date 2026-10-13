cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
import numpy as np
from pathlib import Path

b = Path("artifacts/v1.168-max/cta_max")
mx = np.load(b / "real_sanity_max_2048_full_runner.npy")
pt = np.load(b / "real_sanity_pytorch_same_input_verified.npz")["final"]

print("MAX SHAPE:", mx.shape)
print("PYTORCH SHAPE:", pt.shape)

if mx.shape != pt.shape:
    raise SystemExit("STOP: Output shapes differ")

print("VERIFIED FINAL MAX_DIFF:", np.max(np.abs(mx - pt)))
print("VERIFIED FINAL MATCH:", np.allclose(mx, pt, atol=1e-3, rtol=1e-3))
PY
