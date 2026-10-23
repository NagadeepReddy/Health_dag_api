cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

old = "    install_cta_spawn_entry()"
assert s.count(old) == 1, "Launcher differs; no changes made"

if "register_cta_routes()" not in s:
    new = '''    install_cta_spawn_entry()
    from maxserve_cta_extension.cta_router import register_cta_routes
    register_cta_routes()'''
    s = s.replace(old, new)

compile(s, str(p), "exec")
p.write_text(s)

print("NATIVE CTA ROUTER WIRED: SYNTAX PASS")
PY
