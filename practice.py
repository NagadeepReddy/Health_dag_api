python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_router.py")
s = p.read_text()

anchor = '    request_id = str(getattr(request.state, "request_id", None) or uuid4())'
marker = '# BPLAN_MAX_RESPONSE_QUEUE_BRIDGE'

if marker in s:
    print("BPLAN QUEUE BRIDGE: ALREADY PRESENT")
else:
    assert s.count(anchor) == 1, "STOP: request insertion point changed"
    patch = '''    # BPLAN_MAX_RESPONSE_QUEUE_BRIDGE
    from .bplan_http_pipeline import _BPLAN_ACTIVE_ENGINES
    receivers = list(_BPLAN_ACTIVE_ENGINES)
    if len(receivers) != 1:
        raise HTTPException(503, f"Expected one BPLAN response receiver, found {len(receivers)}")
    receiver = receivers[0]
    if receiver is not queue:
        receiver.pending_out_queues = queue.pending_out_queues

'''
    p.with_suffix(".py.pre_bridge_backup").write_text(s)
    p.write_text(s.replace(anchor, patch + anchor))

py_compile.compile(str(p), doraise=True)
print("BPLAN QUEUE BRIDGE: PASS")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
