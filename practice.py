cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
p = base / "cta_spawn_worker.py"
registration = (base / "cta_worker_registration.py").read_text()
s = p.read_text()

old = "pipeline.cta_adapter = CTAWorkerAdapter(CTA, attach_max)"
new = """pipeline._cta_adapter = CTAWorkerAdapter(CTA, attach_max)
        pipeline.cta_adapter = pipeline._cta_adapter"""

assert s.count(old) == 1, "Unexpected wrapper; no changes made"
assert '"_cta_adapter"' in registration, "Scheduler contract differs"

updated = s.replace(old, new)
compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA ADAPTER AND SCHEDULER WIRING: FIXED")
print("SYNTAX: PASS")
PY
