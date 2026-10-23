cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = "queue.stream(request_id, context)"
new = "queue.open_channel(request_id, context)"

if old in s:
    p.with_suffix(".py.bak").write_text(s)
    p.write_text(s.replace(old, new, 1))
    print("Native queue dispatch FIXED")
elif new in s:
    print("Already fixed")
else:
    print("Queue call differs; no changes made")

py_compile.compile(str(p), doraise=True)
print("Syntax PASS")
PY
