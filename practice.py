python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/cta_max_native_release_candidate_20261028")
http = root / "cta_http_pipeline.py"
router = root / "cta_router.py"

assert http.is_file() and router.is_file(), "STOP: Release files missing"

h = http.read_text()
r = router.read_text()

assert h.count("_CTA_ACTIVE_ENGINES = []") == 1
assert h.count("async def _cta_fast_response_worker(self):") == 1
assert h.count("async def _cta_traced_response_worker(self):") == 1
assert r.count("receiver_queue.pending_out_queues = queue.pending_out_queues") == 1
assert "_CTA_EXTRA_RESPONSE_QUEUES" not in h
assert "_CTA_EXTRA_RESPONSE_QUEUES" not in r

start = h.index("async def _cta_fast_response_worker(self):")
end = h.index("async def _cta_traced_response_worker(self):", start)

replacement = '''async def _cta_fast_response_worker(self):
    """Receive CTA replies from both native MAX queue connections."""
    import asyncio
    import queue as std_queue

    while True:
        received = False
        sources = [self] + [
            q for q in _CTA_EXTRA_RESPONSE_QUEUES if q is not self
        ]

        for source in sources:
            try:
                responses = source.response_queue.get_nowait()
            except std_queue.Empty:
                continue

            received = True

            for request_id, response in responses.items():
                pending = self.pending_out_queues.get(request_id)

                if pending is not None:
                    await pending.put(response)
                    print(
                        "CTA HTTP RESPONSE DELIVERED:",
                        request_id,
                        "source:",
                        id(source),
                        flush=True,
                    )
                else:
                    self.cancel_queue.put_nowait([request_id])
                    print(
                        "CTA RESPONSE WITHOUT PENDING REQUEST:",
                        request_id,
                        flush=True,
                    )

        if not received:
            if not self.is_worker_healthy():
                raise RuntimeError("CTA native worker unhealthy")
            await asyncio.sleep(0.01)


'''

new_h = h.replace(
    "_CTA_ACTIVE_ENGINES = []",
    "_CTA_ACTIVE_ENGINES = []\n_CTA_EXTRA_RESPONSE_QUEUES = []",
    1,
)
new_h = new_h[:new_h.index(
    "async def _cta_fast_response_worker(self):"
)] + replacement + new_h[new_h.index(
    "async def _cta_traced_response_worker(self):"
):]

anchor = "receiver_queue.pending_out_queues = queue.pending_out_queues"
new_r = r.replace(
    anchor,
    anchor + '''
        from .cta_http_pipeline import _CTA_EXTRA_RESPONSE_QUEUES
        if all(q is not queue for q in _CTA_EXTRA_RESPONSE_QUEUES):
            _CTA_EXTRA_RESPONSE_QUEUES.append(queue)
''',
    1,
)

ast.parse(new_h)
ast.parse(new_r)

for p in (http, router):
    backup = p.with_name(p.name + ".before_dual_queue_fix.bak")
    assert not backup.exists(), f"STOP: Backup exists: {backup}"

for p in (http, router):
    backup = p.with_name(p.name + ".before_dual_queue_fix.bak")
    backup.write_bytes(p.read_bytes())

http.write_text(new_h)
router.write_text(new_r)

print("DUAL-QUEUE RESPONSE FIX: INSTALLED")
print("REQUEST PATH: PRESERVED")
print("BOTH RESPONSE SOCKETS: POLLED")
print("REQUEST-ID MATCHING: PRESERVED")
print("PYTHON SYNTAX: PASS")
print("BACKUPS: CREATED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX PACKAGE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
