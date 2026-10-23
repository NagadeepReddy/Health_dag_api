cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()
old = 'getattr(pipeline, "_engine_queue", None)'
new = 'getattr(pipeline, "engine_queue", None)'

if old in s:
    p.with_suffix(".py.bak").write_text(s)
    p.write_text(s.replace(old, new))
    print("Queue connection fixed")
elif new in s:
    print("Already fixed")
else:
    print("Different queue code; no changes made")

py_compile.compile(str(p), doraise=True)
print("Syntax PASS")
PY
