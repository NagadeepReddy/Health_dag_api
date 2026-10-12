python - <<'PY'
import numpy as np
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
pt_file = base / "real_sanity_pytorch_branches.npz"
mx_file = base / "real_sanity_max_branches.npz"

assert pt_file.is_file() and mx_file.is_file()

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

pt = np.load(pt_file)
mx = np.load(mx_file)

print("=== BRANCH WIRING DIAGNOSTIC ===")
print(f"{'PYTORCH':<12} {'BEST MAX MATCH':<16} {'MEAN DIFF':>12} {'EXPECTED':>10}")

for name in names:
    a = pt[name].reshape(-1).astype(np.float64)

    candidates = []
    for other in names:
        b = mx[other].reshape(-1).astype(np.float64)
        assert a.shape == b.shape == (256,)

        diff = float(np.mean(np.abs(a - b)))
        candidates.append((diff, other))

    candidates.sort()
    best_diff, best_name = candidates[0]

    print(
        f"{name:<12} {best_name:<16} "
        f"{best_diff:>12.6f} "
        f"{str(best_name == name):>10}"
    )

print("\n=== BRANCH VALUE RANGES ===")
for name in names:
    a = pt[name]
    b = mx[name]
    print(
        f"{name:<10} "
        f"PT mean={a.mean():>9.4f} std={a.std():>9.4f} | "
        f"MAX mean={b.mean():>9.4f} std={b.std():>9.4f}"
    )

print("\nREAD ONLY — NO FILES MODIFIED")
PY
