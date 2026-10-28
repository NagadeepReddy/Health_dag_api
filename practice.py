cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
router = base / "cta_router.py"
pipeline = base / "cta_http_pipeline.py"

r = router.read_text()
p = pipeline.read_text()

assert "CTA ROUTE QUEUE ID:" not in r, "STOP: route already instrumented"
assert "CTA RECEIVER ENGINE ID:" not in p, "STOP: receiver already instrumented"

route_anchor = "    request_id = request.state.request_id"
receiver_anchor = '    print("CTA RESPONSE WORKER LOOP: START", flush=True)'
socket_anchor = '                        "CTA RESPONSE ID MATCH:",'

assert r.count(route_anchor) == 1, "STOP: route anchor changed"
assert p.count(receiver_anchor) == 1, "STOP: receiver anchor changed"
assert p.count(socket_anchor) == 1, "STOP: socket anchor changed"

r2 = r.replace(
    route_anchor,
    route_anchor + '''
    import time
    print(
        "CTA ROUTE QUEUE ID:", id(queue),
        "TIME:", time.monotonic(),
        "PENDING:", len(getattr(queue, "pending_out_queues", {})),
        flush=True,
    )''',
    1
)

p2 = p.replace(
    receiver_anchor,
    '''    import time
    print(
        "CTA RECEIVER ENGINE ID:", id(self),
        "TIME:", time.monotonic(),
        flush=True,
    )
''' + receiver_anchor,
    1
)

p2 = p2.replace(
    socket_anchor,
    '''                        "ENGINE_ID:", id(engine),
                        "TIME:", __import__("time").monotonic(),
''' + socket_anchor,
    1
)

ast.parse(r2)
ast.parse(p2)

backups = [
    (router, router.with_name(router.name + ".before_queue_identity.bak"), r2),
    (pipeline, pipeline.with_name(pipeline.name + ".before_queue_identity.bak"), p2),
]

assert all(not backup.exists() for _, backup, _ in backups), \
    "STOP: backup already exists"

for original, backup, updated in backups:
    backup.write_bytes(original.read_bytes())
    original.write_text(updated)

print("QUEUE IDENTITY DIAGNOSTICS: INSTALLED")
print("BACKUPS: PASS")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
