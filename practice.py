python3 - <<'PY'
from pathlib import Path
import shutil

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max")
matches = [
    p for p in root.rglob("grecbase_fusion_full_head_72_max.py")
    if "batch2" in str(p.parent).lower()
]

if len(matches) != 1:
    print("STOP: Expected one staged batch-2 graph, found:", len(matches))
    for p in matches:
        print(p)
else:
    source = matches[0]
    target = source.with_name("grecbase_fusion_full_head_72_batch2.py")
    if target.exists():
        print("PRESERVED EXISTING:", target)
    else:
        shutil.copy2(source, target)
        print("BATCH-2 WORKING FILE CREATED:", target)
    print("ORIGINAL GRAPH: UNCHANGED")
PY
