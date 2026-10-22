cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension")
for name in ("cta_spawn_worker.py", "cta_scheduler_factory.py", "cta_worker_registration.py"):
    ast.parse((p / name).read_text())
    print(name, "SYNTAX PASS")

print("NATIVE CTA FILES: PASS")
PY
