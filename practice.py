
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8")
shared = root / "max_shared_infra/python/max_runtime_shared"
model = (
    root / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)

targets = [
    (shared / "scheduler_hooks.py", 1, 180),
    (shared / "router_contract.py", 1, 180),
    (shared / "worker_lifecycle.py", 1, 180),
    (model / "pzaas_native_launcher.py", 1, 90),
    (model / "pzaas_spawn_worker.py", 1, 47),
    (model / "pzaas_router.py", 48, 64),
]

print("=== SHARED MAX LIVE WIRING SOURCE ===")

for path, start, end in targets:
    print(f"\n=== {path.name} ===")
    if not path.is_file():
        raise SystemExit(f"STOP: Missing {path}")
    lines = path.read_text().splitlines()
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1:3}: {lines[i]}")

print("\n=== RESULT ===")
print("SHARED WIRING SOURCE: CAPTURED")
print("ORIGINAL MODEL FILES: UNCHANGED")
print("EXISTING HANDOFFS: UNCHANGED")
print("NO TESTS REPEATED")
print("NEXT: ISOLATED LIVE INTEGRATION")
PY
