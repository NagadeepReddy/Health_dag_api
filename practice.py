cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

changes = {
    "from cta_worker_registration import install_cta_scheduler_hook":
    "from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook",

    "from cta_worker_adapter import CTAWorkerAdapter":
    "from maxserve_cta_extension.cta_worker_adapter import CTAWorkerAdapter",
}

for old, new in changes.items():
    assert old in s or new in s, f"Unexpected code: {old}"
    s = s.replace(old, new)

compile(s, str(p), "exec")
p.write_text(s)
print("CTA WORKER PACKAGE IMPORTS: FIXED")
print("SYNTAX: PASS")
PY
