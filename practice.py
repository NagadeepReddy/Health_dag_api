python3 - <<'PY'
from pathlib import Path

base = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")

for p in sorted(base.rglob("*.py")):
    lines = p.read_text(errors="replace").splitlines()
    hits = [
        i for i, line in enumerate(lines)
        if any(x in line for x in (
            "class BPlanMAXModel",
            "class BPlanMaxModel",
            "def predict(",
            "def predict_batch(",
            "def initialize(",
            "def load_model(",
            "def run_inference("
        ))
    ]
    if not hits:
        continue

    print(f"\n=== {p.relative_to(base)} ===")
    shown = set()
    for i in hits[:8]:
        for j in range(max(0, i-3), min(len(lines), i+28)):
            if j not in shown:
                print(f"{j+1}: {lines[j][:180]}")
                shown.add(j)
PY
