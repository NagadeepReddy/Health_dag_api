python3 -B - <<'PY'
from pathlib import Path

roots = [
    Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"),
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/cta_max"),
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
    Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max"),
]

names = [
    "run_real_sanity_input_adapter.py",
    "grecbase_fusion_full_head_72_max.py",
    "__init__.py",
]

for root in roots:
    print("\nFOLDER:", root)
    print("EXISTS:", root.is_dir())
    if root.is_dir():
        print("PYTHON FILES:", len(list(root.glob("*.py"))))
        for name in names:
            print(" ", name, "FOUND" if (root / name).is_file() else "MISSING")

print("\nREAD-ONLY CHECK COMPLETE")
PY
