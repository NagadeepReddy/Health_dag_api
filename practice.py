python3 - <<'PY'
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

targets = [
    (base / "native_batch2/cta_worker_adapter.py", 57, 145),
    (base / "native_batch2/cta_native_scheduler.py", 70, 125),
]

for path, start, end in targets:
    print(f"\n===== {path.name}:{start}-{end} =====")
    if not path.is_file():
        print("MISSING")
        continue

    lines = path.read_text().splitlines()
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}")

print("\nREAD ONLY: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
