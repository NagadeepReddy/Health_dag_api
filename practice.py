python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py")
lines = p.read_text(errors="replace").splitlines()

sections = [
    ("SECOND BPLAN MODEL CALL", 2470, 2520),
    ("DEFAULT VS REAL INFERENCE DECISION", 3990, 4065),
]

for title, start, end in sections:
    print(f"\n=== {title} ===")
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1][:180]}")
PY
