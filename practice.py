cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

old = "from cta_spawn_worker import install_cta_spawn_entry"
new = "from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry"

assert old in s or new in s, "Unexpected launcher code; no changes made"

s = s.replace(old, new)
s = s.replace(
    "from cta_worker_registration import install_cta_scheduler_hook\n",
    ""
)

compile(s, str(p), "exec")
p.write_text(s)

print("NATIVE LAUNCHER IMPORTS: FIXED")
print("SYNTAX: PASS")
PY
