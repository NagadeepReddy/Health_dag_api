cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
s = p.read_text()

old = '{"request_id": request_id, "body": body}'
new = 'CTAContext(request_id, body)'

if s.count(old) != 1:
    raise SystemExit("Expected request payload not found. No changes made.")

s = s.replace(old, new, 1)

if 'from .cta_context import CTAContext' not in s:
    s = s.replace(
        'async def cta_infer(request: Request):',
        'async def cta_infer(request: Request):\n    from .cta_context import CTAContext',
        1
    )

compile(s, str(p), "exec")
p.write_text(s)

print("CTA NATIVE REQUEST CONTEXT: INSTALLED")
print("ROUTER SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
