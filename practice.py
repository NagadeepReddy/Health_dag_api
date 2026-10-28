cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
source = p.read_text()

old = '''    queue = active[0]
    print(
        "CTA ACTIVE RECEIVER QUEUE SELECTED:",
        id(queue),
        flush=True,
    )'''

new = '''    # Preserve the original queue that successfully delivered CTA
    # requests to the native MAX worker.
    # Share only its pending-response registry with the active receiver.
    receiver_queue = active[0]

    if queue is None:
        raise HTTPException(503, "Native CTA request queue unavailable")

    if queue is not receiver_queue:
        receiver_queue.pending_out_queues = queue.pending_out_queues

    print(
        "CTA QUEUE BRIDGE:",
        "request_queue=", id(queue),
        "receiver_queue=", id(receiver_queue),
        "shared_pending=",
        receiver_queue.pending_out_queues is queue.pending_out_queues,
        flush=True,
    )'''

backup = p.with_name("cta_router.py.before_pending_bridge.bak")

assert source.count(old) == 1, "STOP: existing fix differs"
assert not backup.exists(), "STOP: backup already exists"
assert "CTA QUEUE BRIDGE:" not in source, "STOP: already patched"

updated = source.replace(old, new)
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("CTA REQUEST/RESPONSE BRIDGE: INSTALLED")
print("ORIGINAL WORKER REQUEST QUEUE: PRESERVED")
print("RESPONSE PENDING REGISTRY: SHARED")
print("BACKUP: PASS")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
