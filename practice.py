cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

old = "    install_cta_spawn_entry()"
assert s.count(old) == 1, "Unexpected launcher code; no changes made"

s = s.replace(
    old,
    '    print("CTA: installing worker registration", flush=True)\n'
    '    install_cta_spawn_entry()\n'
    '    print("CTA: worker registration installed", flush=True)'
)

compile(s, str(p), "exec")
p.write_text(s)
print("LAUNCHER DIAGNOSTICS: PASS")
PY
