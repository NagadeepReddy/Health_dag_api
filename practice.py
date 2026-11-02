python3 - <<'PY'
from pathlib import Path
import shutil

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max")
source = root / "maxserve_bplan_extension/bplan_max_dev"
target = root / "bplan_batch2_graph_dev"

graph = target / "grecbase_fusion_full_head_72_max.py"

if not source.is_dir() or not graph.is_file():
    raise SystemExit("STOP: Source directory or isolated graph missing")

copied = []
preserved = []

for src in sorted(source.glob("*.py")):
    dst = target / src.name
    if dst.exists():
        preserved.append(src.name)
    else:
        shutil.copy2(src, dst)
        copied.append(src.name)

print("=== BPLAN BATCH-2 ISOLATION ===")
print("COPIED:", len(copied))
for name in copied:
    print(" +", name)

print("PRESERVED:", len(preserved))
for name in preserved:
    print(" =", name)

print("ORIGINAL SOURCES: UNCHANGED")
print("ISOLATED BATCH-2 FILES:", len(list(target.glob("*.py"))))
print("BPLAN BATCH-2 DEPENDENCY STAGING: COMPLETE")
PY
