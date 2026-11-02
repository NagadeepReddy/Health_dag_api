podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i bplan-debug /opt/venv/bin/python - <<'PY'
import numpy as np
from pathlib import Path

root = Path("/tmp")
pt = root / "bplan_pytorch_scores.npz"
mx = root / "bplan_max_scores.npz"

if not pt.exists() or not mx.exists():
    print("STOP: Saved numerical scores missing")
    raise SystemExit(1)

with np.load(pt) as a, np.load(mx) as b:
    print("=== BPLAN NUMERICAL PARITY ===")

    if a.files != b.files:
        print("FAIL: Model call IDs differ", a.files, b.files)
        raise SystemExit(1)

    passed = bool(a.files)

    for key in a.files:
        x, y = a[key], b[key]
        print("MODEL CALL:", key)
        print("PYTORCH SHAPE:", x.shape)
        print("MAX SHAPE:", y.shape)

        if x.shape != y.shape:
            print("SHAPE MATCH: FAIL")
            passed = False
            continue

        finite = bool(np.isfinite(x).all() and np.isfinite(y).all())
        diff = float(np.max(np.abs(x.astype(np.float64) - y.astype(np.float64))))
        close = finite and bool(np.allclose(x, y, rtol=1e-4, atol=1e-3))

        print("FINITE:", finite)
        print("MAX ABS DIFFERENCE:", diff)
        print("ALLCLOSE:", close)
        passed &= close

    print("BPLAN NUMERICAL PARITY:", "PASS" if passed else "FAIL")
PY
