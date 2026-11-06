
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import hashlib
import difflib

base = Path("/application1/sajjna8")
original = base / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev"
isolated = base / "max_shared_infra/isolated/pzaas_shared_wiring_v1"

names = [
    "pzaas_native_launcher.py",
    "pzaas_spawn_worker.py",
    "pzaas_queue_compat.py",
    "pzaas_worker_registration.py",
    "pzaas_scheduler_factory.py",
    "pzaas_router.py",
]

print("=== PZAAS WORKER STARTUP COMPARISON ===")
print("WORKING SOURCE:", original)
print("ISOLATED SOURCE:", isolated)

for name in names:
    a, b = original / name, isolated / name
    print("\nFILE:", name)
    if not a.is_file() or not b.is_file():
        print("MISSING:", [str(p) for p in (a, b) if not p.is_file()])
        continue
    x = a.read_text().splitlines()
    y = b.read_text().splitlines()
    if x == y:
        print("IDENTICAL")
        continue
    print("DIFFERENT — changed lines:")
    differences = list(difflib.unified_diff(
        x, y, fromfile="working", tofile="isolated", lineterm=""
    ))
    for line in differences[:90]:
        print(line)
    if len(differences) > 90:
        print("... additional differences omitted")

print("\nNO FILES MODIFIED")
print("NO CONTAINERS STARTED")
print("NEXT: CORRECT ISOLATED WORKER STARTUP")
PY
