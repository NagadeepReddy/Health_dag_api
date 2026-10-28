cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

assert "CTA RESPONSE SOCKET RECEIVED" in s, "STOP: tracing missing"
assert "CTA RESPONSE ID MATCH:" not in s, "STOP: already instrumented"

anchor1 = "        return item"
anchor2 = "_cta_original_response_worker = _CTAEngineQueue.response_worker"
anchor3 = '    print("CTA RESPONSE WORKER LOOP: START", flush=True)'

assert s.count(anchor1) == 1, "STOP: return anchor changed"
assert s.count(anchor2) == 1, "STOP: worker anchor changed"
assert s.count(anchor3) == 1, "STOP: startup anchor changed"

s = s.replace(
    anchor1,
    '''        for engine in _CTA_ACTIVE_ENGINES:
            if getattr(engine, "response_queue", None) is self:
                pending = getattr(engine, "pending_out_queues", {})
                if isinstance(item, dict):
                    print(
                        "CTA RESPONSE ID MATCH:",
                        [(repr(k), type(k).__name__, k in pending)
                         for k in item],
                        "PENDING:",
                        [(repr(k), type(k).__name__)
                         for k in pending],
                        flush=True,
                    )
        return item''',
    1
)

s = s.replace(
    anchor2,
    "_CTA_ACTIVE_ENGINES = []\n" + anchor2,
    1
)

s = s.replace(
    anchor3,
    "    _CTA_ACTIVE_ENGINES.append(self)\n" + anchor3,
    1
)

ast.parse(s)

backup = p.with_name(p.name + ".before_id_match_trace.bak")
assert not backup.exists(), "STOP: backup exists"

backup.write_bytes(p.read_bytes())
p.write_text(s)

print("REQUEST-ID MATCH DIAGNOSTIC: INSTALLED")
print("BACKUP: PASS")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
