cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
paths = [
    ("BATCH FUSION", base / "batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py", 18, 78),
    ("BATCH AUX BRANCHES", base / "batch2_candidate/cta_max/grecbase_aux_branches_max.py", 10, 75),
    ("BATCH AUX FEATURES", base / "batch2_candidate/cta_max/grecbase_aux_features_max.py", 10, 65),
    ("WORKING FUSION", base / "cta_max/grecbase_fusion_full_head_72_max.py", 35, 78),
]

for title, path, start, end in paths:
    print("\n===", title, "===")
    if not path.is_file():
        print("MISSING:", path)
        continue
    lines = path.read_text().splitlines()
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}")

print("\nFILES MODIFIED: NONE")
print("MAX STARTED: NO")
PY
