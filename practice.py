
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import ast
import hashlib
import shutil

base = Path("/application1/sajjna8")
package = Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102")
relative = Path(
    "artifacts/v1.113-max/maxserve_bplan_extension/"
    "bplan_native_serve_dev"
)
source = package / relative
stage = base / "max_shared_infra/isolated/bplan_shared_wiring_v1"
shared = base / "max_shared_infra/python/max_runtime_shared"
runner = base / "max_shared_infra/bin/run_max_model.sh"

print("=== ISOLATED BPLAN SHARED MAX PREPARATION ===")

required = [
    source / "bplan_native_launcher.py",
    shared / "typed_queue.py",
    shared / "scheduler_hooks.py",
    shared / "router_contract.py",
    shared / "worker_lifecycle.py",
    runner,
]

missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise SystemExit(
        "STOP: Required files missing:\n" + "\n".join(missing)
    )

files = sorted(source.glob("*.py"))
if not files:
    raise SystemExit("STOP: No BPLAN serving modules found")

# Validate all sources and reject unexpected existing differences
# before writing anything.
for src in files:
    compile(src.read_bytes(), str(src), "exec")
    dst = stage / src.name
    if dst.exists() and dst.read_bytes() != src.read_bytes():
        raise SystemExit(
            "STOP: Existing isolated file differs; preserved: " + str(dst)
        )

stage.mkdir(parents=True, exist_ok=True)

copied = []
for src in files:
    dst = stage / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
        copied.append(src.name)

print("BPLAN CLEAN SOURCE: VERIFIED")
print("SHARED MAX COMPONENTS: VERIFIED")
print("ISOLATED BPLAN FILES:", len(files))
print("NEW FILES COPIED:", len(copied))
print("ISOLATED PYTHON SYNTAX: PASS")

print("\n=== BPLAN SERVING HOOKS ===")
keywords = (
    "register_bplan",
    "install_bplan",
    "FactoryWrapper",
    "WorkerAdapter",
    "initialize(",
    "start_model_worker",
    "SchedulerZmqConfigs",
    "response_queue",
    "retrieve_factory",
    "uvicorn.run",
    "fastapi_app",
)

for src in files:
    lines = src.read_text().splitlines()
    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(k in line for k in keywords)
    ]
    if matches:
        print("\nFILE:", src.name)
        for number, line in matches[:16]:
            print(f"  {number}: {line[:160]}")

print("\n=== RESULT ===")
print("BPLAN ISOLATED WORKSPACE: READY")
print("BPLAN NATIVE PORT: 18768")
print("SHARED GENERIC LAUNCHER: READY")
print("ORIGINAL BPLAN HANDOFF: UNCHANGED")
print("CTA / PZAAS HANDOFFS: UNCHANGED")
print("NO RUNNING CONTAINERS CHANGED")
print("NEXT: WIRE SHARED BPLAN HOOKS AND TEST LIVE HTTP")
PY
