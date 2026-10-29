cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import shutil
import filecmp

src = Path("artifacts/v1.168-max/cta_max")
dst = Path("/application1/cta_max_true_batch_dev_20261028/cta_max")

required = "sibling_context_weights/sibling_context_head.deep_embedding.0.weight.npy"

assert (src / required).is_file(), "STOP: Original sibling weight missing"
assert dst.is_dir(), "STOP: Batch workspace missing"

folders = sorted(
    p for p in src.iterdir()
    if p.is_dir() and p.name.endswith("_weights")
)

assert folders, "STOP: No exported weight directories"

pending = []
for folder in folders:
    for original in folder.rglob("*.npy"):
        target = dst / original.relative_to(src)
        if target.exists():
            assert target.is_file() and filecmp.cmp(
                original, target, shallow=False
            ), f"STOP: Conflicting existing weight: {target}"
        else:
            pending.append((original, target))

needed = sum(p.stat().st_size for p, _ in pending)
assert shutil.disk_usage("/application1").free > needed + 1073741824, \
    "STOP: Insufficient disk space"

for original, target in pending:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(original, target)

assert (dst / required).read_bytes() == (src / required).read_bytes()

print("MAX EXPORTED WEIGHT SETUP: PASS")
print("WEIGHT DIRECTORIES:", len(folders))
print("MISSING WEIGHTS COPIED:", len(pending))
print("SIBLING WEIGHTS: VERIFIED")
print("EXISTING WEIGHTS: PRESERVED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
