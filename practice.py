cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

call = "    register_cta_architecture()\n"

if call not in s:
    target = "    install_cta_spawn_entry()\n"
    assert target in s, "Launcher structure changed; nothing modified"

    addition = (
        "    from maxserve_cta_extension.cta_architecture_registration "
        "import register_cta_architecture\n"
        "    register_cta_architecture()\n"
    )

    s = s.replace(target, addition + target, 1)
    p.write_text(s)

compile(p.read_text(), str(p), "exec")

print("CTA ARCHITECTURE STARTUP REGISTRATION: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY
