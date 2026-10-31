python3 -B - <<'PY'
from pathlib import Path

clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
p = clean / "batch2/cta_max/grecbase_fusion_full_head_72_max.py"

print("=== WEIGHT LOADING CODE ===")
for n, line in enumerate(p.read_text().splitlines(), 1):
    if n <= 100:
        print(f"{n}: {line}")

print("\n=== WEIGHT FOLDERS ===")
for root in [
    Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/grecbase_integration_weights"),
    clean / "batch2/cta_max/grecbase_integration_weights",
]:
    print(root, "FOUND" if root.is_dir() else "MISSING")
    if root.is_dir():
        for f in sorted(root.iterdir()):
            print(" ", f.name)

print("\nREAD-ONLY CHECK COMPLETE")
PY
