P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== ACTUAL MYPLAN RESPONSE ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/bplan_myplan_trace.json")
if not p.is_file():
    print("Response file missing")
else:
    obj = json.loads(p.read_text())
    print(json.dumps(obj, indent=2, default=str)[:3500])
PY

echo "=== EXACT MAX ERROR ==="
"${P[@]}" logs bplan-debug 2>&1 | python3 -c '
import sys
lines = sys.stdin.read().splitlines()
markers = [
    "BPLAN REAL MAX EXECUTION START",
    "BPLAN MAX BACKEND EXECUTION START",
    "Traceback (most recent call last)",
    "BPLAN REAL MAX EXECUTION PASS"
]
hits = [i for i, line in enumerate(lines)
        if any(marker in line for marker in markers)]
if not hits:
    print("No MAX execution or traceback markers found")
else:
    for i in hits[-8:]:
        print("\n--- LOG AT LINE", i + 1, "---")
        for line in lines[max(0, i-2):min(len(lines), i+28)]:
            print(line[:240])
'
