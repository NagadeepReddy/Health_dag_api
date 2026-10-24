python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_id_match_test.log")
lines = p.read_text(errors="replace").splitlines()

terms = (
    "CTA QUEUE CONNECTION", "CTA ACTUAL ENGINE QUEUE",
    "CTA HTTP FANOUT", "CTA REQUEST RECEIVED",
    "CTA MAX REQUEST UNWRAPPED",
    "CTA NATIVE RESPONSE TYPES",
    "CTA WORKER RESPONSE IDS:",
    "CTA NATIVE HTTP STATUS", "CTA RESPONSE:",
    "ValidationError", "TypeError", "KeyError",
    "Traceback", "Error", "Killed"
)

events = [
    x for x in lines
    if any(t in x for t in terms)
    and "CTA WORKER RESPONSE IDS: []" not in x
]

print("=== FIRST IMPORTANT EVENTS ===")
print("\n".join(events[:20]) or "NONE")
print("=== LAST LOG LINES ===")
print("\n".join(lines[-15:]))
PY
