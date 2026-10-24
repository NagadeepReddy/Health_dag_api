python3 - <<'PY'
from pathlib import Path

lines = Path("/tmp/cta_handoff_check.log").read_text(
    errors="replace"
).splitlines()

terms = (
    "CTA QUEUE CONNECTION",
    "CTA ACTUAL ENGINE QUEUE",
    "CTA HTTP FANOUT",
    "HTTP WAITING ID",
    "CTA REQUEST RECEIVED",
    "CTA SOCKET",
    "Traceback",
    "Error",
    "Exception",
)

print("=== REQUEST EXECUTION PATH ===")
for i, line in enumerate(lines):
    if any(t in line for t in terms):
        print(f"{i+1}: {line[:250]}")

print("\n=== FINAL LOG LINES ===")
print("\n".join(lines[-8:]))
PY
