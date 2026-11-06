
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import re

infra = Path("/application1/sajjna8/max_shared_infra")
base = Path(
    "/application1/sajjna8/"
    "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev"
)

files = {
    "NATIVE LAUNCHER": "pzaas_native_launcher.py",
    "QUEUE INSTALLATION": "pzaas_queue_compat.py",
    "SCHEDULER": "pzaas_native_scheduler.py",
    "ROUTER": "pzaas_router.py",
    "WORKER STARTUP": "pzaas_spawn_worker.py",
    "WORKER LIFECYCLE": "pzaas_worker_adapter.py",
}

patterns = {
    "NATIVE LAUNCHER":
        r"queue|scheduler|register|router|worker|spawn|app|uvicorn",
    "QUEUE INSTALLATION":
        r"install|SchedulerZmqConfigs|response_type|response_queue",
    "SCHEDULER":
        r"^class |^def |^    def |queue|scheduler|install",
    "ROUTER":
        r"^def |^async def |register|route|scheduler|queue",
    "WORKER STARTUP":
        r"import |initialize|worker|factory|install|register",
    "WORKER LIFECYCLE":
        r"^class |^    def |initialize|attach_max|predict_raw",
}

print("=== SHARED MAX INTEGRATION POINTS ===")

for label, filename in files.items():
    path = base / filename

    print(f"\n=== {label} ===")
    print("FILE:", filename)

    if not path.is_file():
        print("STOP: EXPECTED FILE MISSING")
        continue

    lines = path.read_text(
        errors="replace"
    ).splitlines()

    matches = [
        i for i, line in enumerate(lines)
        if re.search(
            patterns[label],
            line,
            re.IGNORECASE
        )
    ]

    print("TOTAL LINES:", len(lines))
    print("MATCHING LINES:", len(matches))

    for i in matches[:14]:
        print(f"{i+1:4}: {lines[i][:180]}")

    if len(matches) > 14:
        print(
            "ADDITIONAL MATCHES:",
            len(matches) - 14
        )

print("\n=== SHARED COMPONENTS ===")

for name in (
    "typed_queue",
    "scheduler_hooks",
    "router_contract",
    "worker_lifecycle",
):
    path = (
        infra / "python/max_runtime_shared"
        / f"{name}.py"
    )
    print(
        name,
        "READY" if path.is_file() else "MISSING"
    )

print("\n=== SHARED LAUNCHER ===")

launcher = infra / "bin/run_max_model.sh"

if not launcher.is_file():
    raise SystemExit("STOP: Shared launcher missing")

text = launcher.read_text()

print("LAUNCHER: PRESENT")
print(
    "SHARED PYTHON MOUNT:",
    "PRESENT"
    if "/shared_runtime" in text
    else "NOT YET CONFIGURED"
)

print("\n=== RESULT ===")
print("INTEGRATION ENTRY POINTS: INSPECTED")
print("ORIGINAL HANDOFF: UNCHANGED")
print("NO FILES MODIFIED")
print("NO CONTAINERS STARTED")
print("NEXT: ISOLATED SHARED PYTHON WIRING")
PY
