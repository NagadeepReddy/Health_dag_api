ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
files = [
    ("MAX GRAPH", root / "bplan_max_dev/grecbase_fusion_full_head_72_max.py", 1, 115),
    ("INPUT PREPARATION", root / "bplan_max_dev/run_real_sanity_input_adapter.py", 1, 115),
]

for title, path, start, end in files:
    print(f"\n=== {title} ===")
    if not path.is_file():
        print("MISSING:", path)
        continue
    lines = path.read_text().splitlines()
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}")

print("\nBPLAN BATCH-2 READ-ONLY INSPECTION COMPLETE")
PY
