
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import hashlib
import shutil

base = Path("/application1/sajjna8")
roots = [
    Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031"),
    Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
    base / "rt-pzaas-cta-offers-v1/artifacts/v1.168-max",
]
stage = base / "max_shared_infra/isolated/cta_shared_wiring_v1"
shared = base / "max_shared_infra/python/max_runtime_shared"

print("=== CTA SHARED MAX ADOPTION ===", flush=True)

required_shared = [
    "typed_queue.py",
    "scheduler_hooks.py",
    "router_contract.py",
    "worker_lifecycle.py",
]
for name in required_shared:
    if not (shared / name).is_file():
        raise SystemExit("STOP: Shared component missing: " + name)

candidates = []
for root in roots:
    if root.is_dir():
        candidates += list(root.rglob("cta_native_launcher.py"))

if not candidates:
    raise SystemExit(
        "STOP: Existing CTA native launcher not found; "
        "original files unchanged"
    )

def score(path):
    folder = path.parent
    names = {p.name for p in folder.glob("*.py")}
    return (
        len(names & {
            "cta_router.py",
            "cta_spawn_worker.py",
            "cta_worker_adapter.py",
            "cta_native_scheduler.py",
        }),
        len(names),
    )

source = max(candidates, key=score).parent
files = sorted(source.glob("*.py"))

if len(files) < 2:
    raise SystemExit("STOP: Incomplete CTA serving source")

for src in files:
    compile(src.read_bytes(), str(src), "exec")
    target = stage / src.name
    if target.exists() and target.read_bytes() != src.read_bytes():
        raise SystemExit(
            "STOP: Existing CTA staged file differs: " + src.name
        )

stage.mkdir(parents=True, exist_ok=True)

copied = []
for src in files:
    target = stage / src.name
    if not target.exists():
        shutil.copy2(src, target)
        copied.append(src.name)

print("CTA SOURCE:", source)
print("CTA NATIVE LAUNCHER: FOUND")
print("SHARED COMPONENTS: PASS")
print("ISOLATED MODULES:", len(files))
print("NEW FILES COPIED:", len(copied))
print("PYTHON SYNTAX: PASS")

print("\n=== CTA INTEGRATION POINTS ===")
terms = (
    "register_cta",
    "install_cta",
    "start_model_worker",
    "retrieve_factory",
    "FactoryWrapper",
    "SchedulerZmqConfigs",
    "add_api_route",
    "uvicorn.run",
)
for src in files:
    matches = [
        (i, line.strip())
        for i, line in enumerate(src.read_text().splitlines(), 1)
        if any(term in line for term in terms)
    ]
    if matches:
        print("FILE:", src.name)
        for number, line in matches[:10]:
            print(f"  {number}: {line[:130]}")

print("\n=== RESULT ===")
print("CTA ISOLATED SHARED WORKSPACE: READY")
print("ORIGINAL CTA HANDOFF: UNCHANGED")
print("BPLAN / PZAAS: UNCHANGED")
print("NO CONTAINERS STARTED")
print("NEXT: CTA SHARED WIRING + LIVE HTTP")
PY
