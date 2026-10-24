cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

anchor = 'request_id = request.state.request_id'
diagnostic = '''print(
        "CTA HTTP FANOUT:",
        "background_tasks=", [
            (t.done(), str(t.exception()) if t.done() and not t.cancelled() else "running")
            for t in getattr(pipeline, "_background_tasks", [])
        ],
        "response_worker=", hasattr(queue, "response_worker"),
        "request_id=", request_id,
        flush=True,
    )'''

if "CTA HTTP FANOUT:" not in s:
    assert s.count(anchor) == 1, "Expected anchor missing; unchanged"
    s = s.replace(anchor, anchor + "\n    " + diagnostic, 1)
    compile(s, str(p), "exec")
    p.write_text(s)

print("CTA HTTP FANOUT DIAGNOSTIC: READY")
PY
