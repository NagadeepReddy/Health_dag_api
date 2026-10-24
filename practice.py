python3 - <<'PY'
from pathlib import Path
s = Path("/tmp/cta_dispatch_trace.log").read_text(errors="replace")
for term in (
    "CTA REQUEST RECEIVED",
    "CTA NATIVE RESPONSE TYPES",
    "CTA WORKER RESPONSE IDS: [RequestID",
    "Failed to put message",
    "Socket operation",
    "HTTP PENDING:",
    "RESPONSE RECEIVED:",
    "DISPATCH MATCH:",
    "CTA NATIVE HTTP STATUS",
):
    lines = [x for x in s.splitlines() if term in x]
    print(f"{term}: {lines[-1][:220] if lines else 'NOT FOUND'}")
PY
