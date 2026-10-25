cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
old = "wrapped._cta_wrapped = True"
new = "wrapped._cta_wrapped = True\n        wrapped._cta_native_pipeline = True"
assert s.count(old) == 1, "Expected assignment not found exactly once; no changes made"
p.write_text(s.replace(old, new, 1))
print("CTA native pipeline flag aligned: PASS")
PY
