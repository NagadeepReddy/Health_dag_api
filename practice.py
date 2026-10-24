python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_queue_fix_test.log")
lines = p.read_text(errors="replace").splitlines()

print("=== FIRST WORKER RESPONSE ===")
for i, line in enumerate(lines):
    if "CTA WORKER RESPONSE IDS:" in line and "[]" not in line:
        print("\n".join(lines[max(0, i-10):i+20]))
        break

print("\n=== FIRST RESPONSE DELIVERY ERROR ===")
for i, line in enumerate(lines):
    if any(x in line for x in (
        "Failed to put message",
        "Error in background draining",
        "CTA NATIVE HTTP STATUS",
    )):
        print("\n".join(lines[max(0, i-8):i+8]))
        break
PY
