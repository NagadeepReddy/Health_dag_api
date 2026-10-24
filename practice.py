cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
marker = 'print("CTA_NATIVE_FACTORY_ENTERED", flush=True)'

if marker not in s:
    target = "    def __call__(self):\n"
    assert s.count(target) == 1, "Factory method not found; no changes made"
    s = s.replace(target, target + f"        {marker}\n", 1)
    p.write_text(s)

compile(s, str(p), "exec")
print("CTA FACTORY TRACE READY — Syntax PASS")
PY
