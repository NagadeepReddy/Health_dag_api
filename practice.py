python - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")
assert base.is_dir()

print("=== EXISTING REAL FINAL OUTPUTS ===")

found = []
for p in sorted(base.rglob("*")):
    if p.suffix not in (".npy", ".npz"):
        continue
    if not any(k in p.name.lower() for k in (
        "output", "prediction", "reference", "pytorch", "sanity"
    )):
        continue
    try:
        if p.suffix == ".npy":
            a = np.load(p, mmap_mode="r")
            if a.shape == (1, 10819):
                found.append((p, np.asarray(a)))
        else:
            with np.load(p) as data:
                for key in data.files:
                    if data[key].shape == (1, 10819):
                        found.append((Path(str(p) + ":" + key), data[key].copy()))
    except Exception as e:
        print("SKIPPED:", p.name, str(e)[:100])

for p, a in found:
    print("FILE:", p)
    print("SHAPE:", a.shape, "FINITE:", bool(np.isfinite(a).all()))

pt = [(p,a) for p,a in found if "pytorch" in str(p).lower() or "pt_reference" in str(p).lower()]
mx = [(p,a) for p,a in found if "max" in p.name.lower() and "pytorch" not in p.name.lower()]

if len(pt) == 1 and len(mx) == 1:
    diff = np.abs(pt[0][1].astype(np.float64) - mx[0][1].astype(np.float64))
    print("FINAL MEAN DIFF:", diff.mean())
    print("FINAL MAX DIFF:", diff.max())
    print("NUMERICAL MATCH:", np.allclose(pt[0][1], mx[0][1], rtol=1e-3, atol=1e-3))
else:
    print("FINAL COMPARISON: NEED MATCHING PYTORCH AND MAX OUTPUT FILES")
    print("PYTORCH CANDIDATES:", len(pt), "MAX CANDIDATES:", len(mx))

print("READ ONLY — NO FILES MODIFIED")
PY
