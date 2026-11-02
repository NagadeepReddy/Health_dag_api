python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

sections = [
    (ext / "bplan_max_dev/bplan_max_model_adapter.py", 120, 180),
    (ext / "bplan_max_dev/bplan_native_worker_adapter.py", 1, 50),
    (ext / "bplan_native_serve_dev/bplan_native_scheduler.py", 15, 125),
    (root / "artifacts/v1.113/core-artifact/pipeline.py", 2490, 2580),
]

for path, start, end in sections:
    print(f"\n=== {path.name}: {start}-{end} ===")
    if not path.is_file():
        print("FILE MISSING")
        continue
    lines = path.read_text().splitlines()
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1][:160]}")

print("\nREAD-ONLY INSPECTION COMPLETE")
PY
