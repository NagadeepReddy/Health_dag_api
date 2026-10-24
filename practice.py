python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_context_test.log")
lines = p.read_text(errors="replace").splitlines()

filtered = [
    line for line in lines
    if "CTA WORKER RESPONSE IDS: []" not in line
    and "not use pretrained embedding" not in line
    and "loaded Transfer Model" not in line
]

print("=== ACTUAL FAILURE DETAILS ===")
print("\n".join(filtered[-65:]))
PY
