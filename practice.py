cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = "async def cta_infer(request):"
new = "from fastapi import Request\n\nasync def cta_infer(request: Request):"

if old in s:
    updated = s.replace(old, new, 1)
    compile(updated, str(p), "exec")
    p.with_name(p.name + ".before_request_fix.bak").write_text(s)
    p.write_text(updated)
    print("CTA request annotation FIXED")
elif "async def cta_infer(request: Request):" in s:
    print("Already fixed")
else:
    print("Handler differs; no changes made")

py_compile.compile(str(p), doraise=True)
print("Syntax PASS")
PY
