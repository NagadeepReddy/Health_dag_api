python3 -B - <<'PY'
from pathlib import Path
import filecmp

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
a = root / "batch2/cta_max"
b = root / "artifacts/v1.168-max/cta_max"

if not a.is_dir() or not b.is_dir():
    raise SystemExit("STOP: Model directory missing")

def inventory(folder):
    return {
        str(p.relative_to(folder)): p
        for p in folder.rglob("*")
        if p.is_file() and not p.is_symlink()
    }

A = inventory(a)
B = inventory(b)

only_a = sorted(A.keys() - B.keys())
only_b = sorted(B.keys() - A.keys())
different = sorted(
    k for k in A.keys() & B.keys()
    if not filecmp.cmp(A[k], B[k], shallow=False)
)

print("=== DUPLICATE AUDIT ===")
print("Reference files:", len(A))
print("Mounted files:", len(B))
print("Identical files:", len(A.keys() & B.keys()) - len(different))

for label, items in [
    ("REFERENCE ONLY", only_a),
    ("MOUNTED ONLY", only_b),
    ("DIFFERENT CONTENT", different)
]:
    print(f"\n=== {label}: {len(items)} ===")
    for item in items[:30]:
        print(item)

print("\nAUDIT COMPLETE — NO FILES CHANGED")
PY
