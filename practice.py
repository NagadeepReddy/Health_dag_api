cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = 'router.add_api_route("/cta/infer", cta_infer, methods=["POST"])'
new = old + '\n    router.add_api_route("/cta/predict", cta_infer, methods=["POST"])'

if '"/cta/predict"' in s:
    print("Predict route already registered; no changes made")
elif old in s:
    p.with_suffix(".py.bak").write_text(s)
    p.write_text(s.replace(old, new, 1))
    print("Predict route registered")
else:
    print("Existing handler registration differs; no changes made")

import py_compile
py_compile.compile(str(p), doraise=True)
print("Syntax check PASS")
PY
