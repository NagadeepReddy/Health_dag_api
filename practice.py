python - <<'PY'
from pathlib import Path
from datetime import datetime
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")
files = {
    "PyTorch": base / "real_sanity_pytorch_branches.npz",
    "MAX": base / "real_sanity_max_branches.npz",
}

for name, p in files.items():
    if not p.is_file():
        raise SystemExit(f"MISSING: {p}")
    print(name, "saved:", datetime.fromtimestamp(p.stat().st_mtime))

with np.load(files["PyTorch"]) as pt, np.load(files["MAX"]) as mx:
    keys = sorted(set(pt.files) | set(mx.files))
    passed = 0

    print("\n=== SAVED 8-BRANCH NUMERICAL PARITY ===")
    for key in keys:
        if key not in pt or key not in mx:
            print(key, "MISSING IN ONE REFERENCE")
            continue

        a, b = pt[key], mx[key]
        if a.shape != b.shape:
            print(key, "SHAPE MISMATCH", a.shape, b.shape)
            continue

        diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
        match = bool(np.allclose(a, b, rtol=1e-3, atol=1e-3))
        passed += match

        print(
            key,
            "PASS" if match else "FAIL",
            "max_diff=", float(diff.max())
        )

    print(f"\nRESULT: {passed}/{len(keys)} PASS")
    print("SAVED FILES ONLY — NOTHING MODIFIED")
PY
