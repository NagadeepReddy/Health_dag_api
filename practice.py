python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/cta_max_native_release_candidate_20261028/"
    "cta_http_pipeline.py"
)

assert p.is_file(), f"STOP: Missing {p}"
source = p.read_text()

old = "return await _cta_original_response_worker(self)"
anchor = "async def _cta_traced_response_worker(self):"

assert source.count(old) == 1, "STOP: Receiver differs or is already changed"
assert source.count(anchor) == 1, "STOP: Receiver definition differs"
assert "_cta_fast_response_worker" not in source, "STOP: Fix already installed"

helper = '''
async def _cta_fast_response_worker(self):
    """CTA-only response polling; preserve MAX request-ID dispatch."""
    import asyncio
    import queue as std_queue

    while True:
        try:
            responses = self.response_queue.get_nowait()
        except std_queue.Empty:
            if not self.is_worker_healthy():
                raise RuntimeError("CTA native model worker is not healthy")
            await asyncio.sleep(0.01)
            continue

        for request_id, response in responses.items():
            pending = self.pending_out_queues.get(request_id)
            if pending is not None:
                await pending.put(response)
                print("CTA HTTP RESPONSE DELIVERED:", request_id, flush=True)
            else:
                self.cancel_queue.put_nowait([request_id])
                print("CTA RESPONSE WITHOUT PENDING REQUEST:", request_id, flush=True)


'''

updated = source.replace(anchor, helper + anchor, 1)
updated = updated.replace(
    old,
    "return await _cta_fast_response_worker(self)",
    1
)

ast.parse(updated)

backup = p.with_name("cta_http_pipeline.py.before_concurrency_fix.bak")
assert not backup.exists(), "STOP: Backup already exists"

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("CTA RESPONSE RECEIVER FIX: INSTALLED")
print("RESPONSE POLLING: 10 ms")
print("REQUEST-ID MATCHING: PRESERVED")
print("BACKUP: CREATED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX PACKAGE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
