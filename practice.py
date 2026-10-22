cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py")
s = p.read_text()

old = "from cta_scheduler_factory import create_cta_scheduler"
new = "from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler"

assert s.count(old) == 1, "Expected import not found; no changes made"
updated = s.replace(old, new)

compile(updated, str(p), "exec")
p.write_text(updated)

print("CTA REGISTRATION IMPORT: FIXED")
print("SYNTAX: PASS")
PY
