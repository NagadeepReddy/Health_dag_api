python3 -S -B - <<'PY'
from pathlib import Path
import re

p = Path("/application1/cta_native_concurrency_final.log")
assert p.is_file(), "STOP: Existing concurrency log missing"

terms = (
    "QUEUE BRIDGE",
    "QUEUE ITEM",
    "REQUEST UNWRAPPED",
    "PREDICT_RAW",
    "RESPONSE IDS",
    "RESPONSE QUEUE SEND",
    "RESPONSE WORKER LOOP",
    "HTTP QUEUE",
    "TIMEOUT",
    "CANCELLED",
    "ERROR",
    "EXCEPTION",
    "request_id",
    "wire_request_id",
    "pending_out_queues",
)

lines = p.read_text(errors="replace").splitlines()

print("=== TWO-REQUEST DELIVERY TIMELINE ===")
for number, line in enumerate(lines, 1):
    if any(term.lower() in line.lower() for term in terms):
        if "telemetry.modular.com" in line:
            continue
        print(f"{number}: {line[:350]}")

print("\n=== EVENT COUNTS ===")
for term in (
    "CTA MAX REQUEST UNWRAPPED",
    "CTA PREDICT_RAW: START",
    "CTA RESPONSE WORKER IDS",
    "CTA RESPONSE QUEUE SEND: COMPLETED",
    "CTA HTTP QUEUE ITEM",
    "CTA TIMEOUT TRACEBACK",
):
    count = sum(term in line for line in lines)
    print(f"{term}: {count}")

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
