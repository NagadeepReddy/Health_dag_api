python3 -S -B - <<'PY'
from pathlib import Path

p = Path("/application1/cta_concurrency_retest_20261029.log")
assert p.is_file(), f"STOP: Missing {p}"

events = {
    "RECEIVER START": "CTA RESPONSE WORKER LOOP: START",
    "PREDICTION START": "CTA PREDICT_RAW: START",
    "PREDICTION COMPLETE": "CTA PREDICT_RAW: ELAPSED",
    "WORKER RESPONSE": "CTA WORKER RESPONSE IDS:",
    "RESPONSE SENT": "CTA RESPONSE QUEUE SEND:",
    "PATCHED DELIVERY": "CTA HTTP RESPONSE DELIVERED:",
    "MISSING PENDING": "CTA RESPONSE WITHOUT PENDING REQUEST:",
    "HTTP RECEIVED": "CTA HTTP QUEUE ITEM:",
    "QUEUE BRIDGE": "CTA QUEUE BRIDGE:",
    "TIMEOUT": "CTA TIMEOUT TRACEBACK:",
}

lines = p.read_text(errors="replace").splitlines()

print("=== PATCHED CONCURRENCY EVENT COUNTS ===")
for name, marker in events.items():
    print(f"{name}: {sum(marker in line for line in lines)}")

print("\n=== REQUEST AND RESPONSE TIMELINE ===")
for i, line in enumerate(lines, 1):
    if any(marker in line for marker in events.values()):
        print(f"{i}: {line[:240]}")

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
