python3 - <<'PY'
from pathlib import Path

lines = Path("/tmp/cta_context_test.log").read_text(errors="replace").splitlines()

for i, line in enumerate(lines):
    if any(x in line for x in (
        "ERROR:max.serve",
        "Error occurred",
        "CTA REQUEST RECEIVED",
        "CTA HTTP FANOUT",
        "CTA ACTUAL ENGINE QUEUE",
        "CTA WORKER RESPONSE IDS:"
    )):
        if "CTA WORKER RESPONSE IDS: []" in line:
            continue
        print(f"\n=== LOG LINE {i+1} ===")
        print("\n".join(lines[max(0,i-3):min(len(lines),i+12)]))
        if "ERROR" in line or "Error occurred" in line:
            break
PY
