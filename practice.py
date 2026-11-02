python3 - <<'PY'
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")

for name in (
    "bplan_max_dev/bplan_max_model_adapter.py",
    "bplan_max_dev/bplan_native_worker_adapter.py",
):
    p = base / name
    print(f"\n========== {name} ==========")

    if not p.is_file():
        print("FILE NOT FOUND")
        continue

    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines[:220], 1):
        print(f"{i:4}: {line}")

    if len(lines) > 220:
        print(f"... {len(lines)-220} additional lines")
PY
