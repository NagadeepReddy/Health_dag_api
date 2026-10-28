cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_safe_probe.py")
s = p.read_text()

anchor = '            body = json.loads(sample.read_text())'

check = '''            import time
            engine = getattr(
                getattr(app.state, "pipeline", None),
                "_engine_queue", None
            )
            if engine is None:
                raise RuntimeError("CTA engine queue missing")

            for attempt in range(30):
                if engine.is_worker_healthy():
                    print("CTA WORKER HEALTH: PASS", flush=True)
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError(
                    "CTA worker never became healthy; request not sent"
                )

'''

if "CTA WORKER HEALTH: PASS" in s:
    print("READINESS CHECK: ALREADY INSTALLED")
else:
    assert s.count(anchor) == 1, "STOP: Test structure differs"
    updated = s.replace(anchor, check + anchor)
    ast.parse(updated)
    p.write_text(updated)
    print("WORKER READINESS CHECK: INSTALLED")

print("DS CODE: UNCHANGED")
PY
