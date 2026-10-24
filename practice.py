python3 - <<'PY'
from pathlib import Path

lines = Path("/tmp/cta_final_verify.log").read_text(
    errors="replace"
).splitlines()

print("=== FIRST ERROR ===")
for i, line in enumerate(lines):
    if any(x in line for x in (
        "Traceback (most recent",
        "ValidationError:",
        "KeyError:",
        "TypeError:",
        "RuntimeError:",
        "MemoryError:",
    )):
        print("\n".join(lines[max(0, i-5):i+18]))
        break
else:
    print("No Python exception found")

print("\n=== LAST IMPORTANT EVENTS ===")
events = [
    x for x in lines
    if any(t in x for t in (
        "CTA REQUEST RECEIVED",
        "CTA MAX REQUEST UNWRAPPED",
        "CTA NATIVE RESPONSE TYPES",
        "CTA WORKER RESPONSE IDS:",
        "CTA NATIVE HTTP STATUS",
        "CTA RESPONSE:",
    ))
    and "RESPONSE IDS: []" not in x
]
print("\n".join(events[-12:]) or "No matching events")
PY
