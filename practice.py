cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
router = base / "cta_router.py"
pipeline = base / "cta_http_pipeline.py"
backup = base / "cta_router.py.before_queue_fix.bak"

source = router.read_text()
receiver = pipeline.read_text()

anchor = '    queue = getattr(pipeline, "_engine_queue", None)'
marker = "CTA ACTIVE RECEIVER QUEUE SELECTED:"

assert source.count(anchor) == 1, "STOP: Route structure changed"
assert marker not in source, "STOP: Fix already installed"
assert not backup.exists(), "STOP: Backup already exists"
assert "_CTA_ACTIVE_ENGINES.append(self)" in receiver, \
    "STOP: Receiver registration unavailable"

replacement = anchor + '''

    # CTA-only integration: use the EngineQueue whose response worker
    # actually receives MAX results, not a separate pipeline queue.
    from .cta_http_pipeline import _CTA_ACTIVE_ENGINES

    active = [
        engine for engine in _CTA_ACTIVE_ENGINES
        if getattr(engine, "response_queue", None) is not None
    ]

    if len(active) != 1:
        raise HTTPException(
            503,
            "Expected exactly one active native MAX response receiver"
        )

    receiver_queue = active[0]
    print(
        "CTA ACTIVE RECEIVER QUEUE SELECTED:",
        "old=", id(queue),
        "new=", id(receiver_queue),
        flush=True,
    )
    queue = receiver_queue'''

updated = source.replace(anchor, replacement, 1)

ast.parse(updated)

shutil.copy2(router, backup)
router.write_text(updated)

print("CTA QUEUE OWNERSHIP FIX: INSTALLED")
print("BACKUP: PASS")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
