cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path(
    "artifacts/v1.168-max/maxserve_cta_extension/"
    "cta_http_pipeline.py"
)

source = p.read_text()
backup = p.with_name(p.name + ".before_response_trace.bak")

anchor = "        return _cta_original_get_nowait(self)"
marker = "CTA RESPONSE SOCKET RECEIVED"

assert source.count(anchor) == 1, "STOP: unexpected receiver implementation"
assert marker not in source, "STOP: tracing already installed"
assert not backup.exists(), "STOP: backup already exists"

updated = source.replace(
    anchor,
    """        item = _cta_original_get_nowait(self)
        print(
            "CTA RESPONSE SOCKET RECEIVED:",
            type(item).__name__,
            "ids=",
            [str(k) for k in item.keys()] if isinstance(item, dict) else "N/A",
            flush=True,
        )
        return item""",
    1,
)

updated += """

# CTA-only diagnostic: trace the MAX response-worker lifecycle.
from max.serve.scheduler.queues import EngineQueue as _CTAEngineQueue

_cta_original_response_worker = _CTAEngineQueue.response_worker

async def _cta_traced_response_worker(self):
    print("CTA RESPONSE WORKER LOOP: START", flush=True)
    try:
        return await _cta_original_response_worker(self)
    except BaseException as exc:
        print(
            "CTA RESPONSE WORKER LOOP: EXIT",
            type(exc).__name__,
            repr(exc),
            flush=True,
        )
        raise

_CTAEngineQueue.response_worker = _cta_traced_response_worker
"""

ast.parse(updated)
shutil.copy2(p, backup)
p.write_text(updated)

print("RESPONSE RECEIVER DIAGNOSTICS: INSTALLED")
print("BACKUP: PASS")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
