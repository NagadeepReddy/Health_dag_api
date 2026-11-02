python3 - <<'PY'
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")

targets = {
    "bplan_router.py": (1, 150),
    "bplan_native_scheduler.py": (43, 125),
    "bplan_http_pipeline.py": (1, 115),
}

for name, (start, end) in targets.items():
    p = base / name
    print(f"\n========== {name} ==========")
    if not p.is_file():
        print("NOT FOUND")
        continue
    lines = p.read_text(errors="replace").splitlines()
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1:4}: {lines[i][:170]}")
PY
