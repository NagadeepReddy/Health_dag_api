cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import re

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

if "register_cta_architecture()" in s:
    print("CTA REGISTRATION ALREADY CONNECTED")
else:
    m = re.search(r'^([ \t]*)install_cta_spawn_entry\(\)\s*$', s, re.M)
    if not m:
        raise SystemExit("Launcher hook not found — no changes made")

    indent = m.group(1)
    addition = (
        indent + "from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture\n"
        + indent + "register_cta_architecture()\n"
    )
    s = s[:m.start()] + addition + s[m.start():]
    p.write_text(s)
    print("CTA REGISTRATION CONNECTED TO LAUNCHER")

PY

python3 -m py_compile \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  && echo "CTA LAUNCHER SYNTAX PASS"
