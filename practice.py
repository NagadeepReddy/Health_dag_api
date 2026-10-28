cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
router = base / "cta_router.py"
pipeline = base / "cta_http_pipeline.py"

source = router.read_text()
receiver = pipeline.read_text()
anchor = '    queue = getattr(pipeline, "_engine_queue", None)'
marker = "CTA ACTIVE RECEIVER QUEUE SELECTED:"

if marker in source:
    print("QUEUE FIX: ALREADY PRESENT — NO CHANGES")
elif source.count(anchor) != 1:
    print("STOP: Unexpected route structure — NO CHANGES")
elif "_CTA_ACTIVE_ENGINES.append(self)" not in receiver:
    print("STOP: Receiver registry unavailable — NO CHANGES")
else:
    replacement = anchor + '''

    # CTA development integration: route requests to the queue
    # whose response worker is receiving native MAX results.
    from .cta_http_pipeline import _CTA_ACTIVE_ENGINES

    active = list({
        id(engine): engine
        for engine in _CTA_ACTIVE_ENGINES
        if getattr(engine, "response_queue", None) is not None
    }.values())

    if len(active) != 1:
        raise HTTPException(
            503,
            f"Expected one MAX response receiver, found {len(active)}"
        )

    queue = active[0]
    print(
        "CTA ACTIVE RECEIVER QUEUE SELECTED:",
        id(queue),
        flush=True,
    )'''

    updated = source.replace(anchor, replacement, 1)
    ast.parse(updated)

    backup = router.with_name("cta_router.py.before_receiver_alignment.bak")
    if backup.exists():
        print("STOP: Backup already exists — NO CHANGES")
    else:
        backup.write_bytes(router.read_bytes())
        router.write_text(updated)
        print("QUEUE ALIGNMENT FIX: INSTALLED")
        print("BACKUP: PASS")
        print("SYNTAX: PASS")

print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
