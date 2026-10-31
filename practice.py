python3 -B - <<'PY'
from pathlib import Path
from collections import defaultdict

roots = [
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
    Path("/application1/cta_max_true_batch_dev_20261028"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max"),
]

found = defaultdict(list)

for root in roots:
    if not root.is_dir():
        continue
    for p in root.rglob("*.npy"):
        if "__pycache__" not in p.parts:
            found[str(p.parent)].append(p.name)

print("=== NUMPY WEIGHT LOCATIONS ===")
for folder, names in sorted(found.items()):
    print("FOLDER:", folder)
    print("COUNT:", len(names))
    for name in sorted(names):
        if "seq_dense" in name or "rotary_emb" in name:
            print("  IMPORTANT:", name)

print("TOTAL NUMPY FILES:", sum(map(len, found.values())))
print("READ-ONLY CHECK COMPLETE")
PY
