python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/pipeline.py")
lines = p.read_text(errors="replace").splitlines()

sections = [
    ("POSTPROCESS ENTRY", 2608, 2645),
    ("DISNEY / TIER RECOMMENDATIONS", 3200, 3300),
    ("FALLBACK TO FINAL RESPONSE", 3996, 4055),
]

for title, start, end in sections:
    print(f"\n=== {title} ===")
    for n in range(start, min(end, len(lines)) + 1):
        line = lines[n-1]
        if title == "DISNEY / TIER RECOMMENDATIONS":
            if not any(x in line.lower() for x in (
                "disney", "tiergroup", "perk", "append",
                "extend", "3399", "4346", "4347", "4348"
            )):
                continue
        print(f"{n}: {line[:180]}")
PY
