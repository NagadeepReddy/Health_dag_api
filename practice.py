python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py")
lines = p.read_text(errors="replace").splitlines()

for label, start, end in [
    ("ORIGINAL INFERENCE", 1993, 2085),
    ("ORIGINAL PREDICT_RAW", 3933, 4015),
]:
    print(f"\n========== {label} ==========")
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1}: {lines[i][:180]}")

print("\n=== MAX CALL SITES IN ORIGINAL PIPELINE ===")
for i, line in enumerate(lines):
    if any(x in line for x in (
        "self.bplan_model(",
        "self.bplan_model.",
        "self.inference(",
        "self.base_model(",
    )):
        print(f"{i+1}: {line.strip()[:180]}")
PY
