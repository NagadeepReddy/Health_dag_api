python - <<'PY'
from pathlib import Path
import numpy as np

B = Path("artifacts/v1.168-max/cta_max")
ATOL = 1e-3
RTOL = 1e-3

print("\n========== CTA OFFERS v1.168 FINAL PARITY AUDIT ==========")

required = [
    "real_sanity_model_in.pt",
    "real_sanity_max_output.npy",
    "real_sanity_pytorch_output.npy",
    "real_sanity_max_branches.npz",
    "real_sanity_pytorch_branches.npz",
]

for name in required:
    p = B / name
    print(f"{name}: {'FOUND' if p.is_file() else 'MISSING'}")

if any(not (B / n).is_file() for n in required):
    raise SystemExit("BLOCKED: Required saved artifacts missing")

def compare(label, pt, mx):
    pt = np.asarray(pt)
    mx = np.asarray(mx)

    print(f"\n--- {label} ---")
    print("PYTORCH SHAPE:", pt.shape)
    print("MAX SHAPE:", mx.shape)

    if pt.shape != mx.shape:
        print("RESULT: SHAPE MISMATCH")
        return False, float("inf")

    try:
        a = pt.astype(np.float64)
        b = mx.astype(np.float64)
    except (TypeError, ValueError):
        print("RESULT: NON-NUMERIC DATA")
        return False, float("inf")

    finite = bool(np.isfinite(a).all() and np.isfinite(b).all())
    if not finite:
        print("RESULT: NON-FINITE VALUES")
        return False, float("inf")

    diff = np.abs(a - b)
    maximum = float(diff.max()) if diff.size else 0.0
    mean = float(diff.mean()) if diff.size else 0.0
    match = bool(np.allclose(a, b, atol=ATOL, rtol=RTOL))
    failures = int(np.count_nonzero(diff > (ATOL + RTOL * np.abs(a))))

    print("MAX DIFF:", maximum)
    print("MEAN DIFF:", mean)
    print("ELEMENTS OUTSIDE TOLERANCE:", failures)
    print("MATCH:", match)

    if not match and diff.size:
        idx = np.unravel_index(np.argmax(diff), diff.shape)
        print("WORST INDEX:", idx)
        print("PYTORCH VALUE:", a[idx])
        print("MAX VALUE:", b[idx])

    return match, maximum

pt = np.load(B / "real_sanity_pytorch_output.npy")
mx = np.load(B / "real_sanity_max_output.npy")

final_match, _ = compare("FINAL CTA OUTPUT", pt, mx)
dimension_match = pt.shape == mx.shape and pt.size == 10819

print("\n========== REAL EIGHT-BRANCH COMPARISON ==========")

results = []
with np.load(B / "real_sanity_pytorch_branches.npz") as p, \
     np.load(B / "real_sanity_max_branches.npz") as m:

    pk = set(p.files)
    mk = set(m.files)

    print("PYTORCH BRANCH KEYS:", sorted(pk))
    print("MAX BRANCH KEYS:", sorted(mk))

    for key in sorted(pk & mk):
        matched, error = compare(key, p[key], m[key])
        results.append((key, matched, error))

    print("\nONLY IN PYTORCH:", sorted(pk - mk))
    print("ONLY IN MAX:", sorted(mk - pk))

    keys_aligned = pk == mk

print("\n========== FINAL RESULTS ==========")
print("REAL INPUT AVAILABLE:", (B / "real_sanity_model_in.pt").is_file())
print("OUTPUT DIMENSION 10819:", dimension_match)
print("FINAL OUTPUT PARITY:", "PASS" if final_match else "FAIL")
print("BRANCH KEYS ALIGNED:", keys_aligned)

for key, matched, error in sorted(results, key=lambda x: x[2], reverse=True):
    print(f"BRANCH {key}: {'PASS' if matched else 'FAIL'} | MAX DIFF {error:.8g}")

print("\nNEXT DECISION:")
if final_match and dimension_match:
    print("NUMERICAL PARITY PASSED.")
    print("Remaining: real JSON pipeline, scoring, serving, CPU/GPU validation.")
else:
    print("NUMERICAL PARITY NOT YET PASSED.")
    print("Fix the highest-error branch using existing saved references.")
    print("Do not rebuild already validated components.")

print("\nORIGINAL PYTORCH AND DS CODE UNCHANGED")
print("READ ONLY - NO FILES MODIFIED")
PY
