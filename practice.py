python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_queue_fix_test.log")
lines = p.read_text(errors="replace").splitlines()

terms = (
    "CTA MAX REQUEST UNWRAPPED",
    "CTA REQUEST RECEIVED",
    "CTA WORKER RESPONSE IDS:",
    "CTA NATIVE HTTP STATUS",
    "CTA RESPONSE:",
    "Failed to put message",
    "Error in background draining",
)

print("=== NATIVE REQUEST / RESPONSE HANDOFF ===")
for line in lines:
    if any(t in line for t in terms):
        if "CTA WORKER RESPONSE IDS: []" not in line:
            print(line[:350])
PY
