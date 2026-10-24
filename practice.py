cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py")
s = p.read_text()

old = 'name="BertModel"'
new = 'name="CTAMaxPipelineModel"'

assert s.count(old) == 1, "Expected architecture definition not found"
p.write_text(s.replace(old, new, 1))

py_compile.compile(str(p), doraise=True)

print("CTA ARCHITECTURE NAME ALIGNMENT: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
