cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py")
s = p.read_text()

old = 'getattr(pipeline, "_cta_adapter", None)'
new = 'getattr(pipeline, "cta_adapter", None)'

assert s.count(old) == 1, "Expected pattern not found; no changes made"

updated = s.replace(old, new)
compile(updated, str(p), "exec")

p.with_suffix(".adapter_fix.bak").write_text(s)
p.write_text(updated)

print("CTA ADAPTER NAME FIXED")
print("Syntax PASS")
PY
