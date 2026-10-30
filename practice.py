python3 -B - <<'PY'
import json
import subprocess
from pathlib import Path

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
stage = dev / "native_batch2_release_candidate/maxserve_cta_extension"

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

if not stage.is_dir():
    raise SystemExit("STOP: Host staging directory missing")

ids = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(
        subprocess.check_output(P + ["inspect", cid], text=True)
    )[0]
    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        ids.append(cid)

if len(ids) != 1:
    raise SystemExit("STOP: Expected one existing development container")

code = r'''
import sys
import importlib
import inspect
from pathlib import Path

root = Path("/batch2/native_batch2_release_candidate")
pkg = root / "maxserve_cta_extension"

required = [
    pkg / "cta_worker_adapter.py",
    pkg / "cta_native_scheduler.py",
    pkg / "cta_scheduler_factory.py",
    Path("/batch2/real_max_batch2_backend.py")
]

for p in required:
    if not p.is_file():
        raise SystemExit(f"STOP: Container file missing: {p}")

print("STAGED PACKAGE VISIBLE: PASS", flush=True)

sys.path.insert(0, str(root))

adapter = importlib.import_module(
    "maxserve_cta_extension.cta_worker_adapter"
)
scheduler = importlib.import_module(
    "maxserve_cta_extension.cta_native_scheduler"
)
factory = importlib.import_module(
    "maxserve_cta_extension.cta_scheduler_factory"
)

for module in (adapter, scheduler, factory):
    if Path(module.__file__).resolve().parent != pkg.resolve():
        raise RuntimeError("Wrong module imported: " + module.__name__)

classes = [
    cls for _, cls in inspect.getmembers(adapter, inspect.isclass)
    if cls.__module__ == adapter.__name__
    and callable(getattr(cls, "predict_batch", None))
]

assert len(classes) == 1, "Batch adapter unavailable"

assert callable(
    getattr(scheduler.CTANativeScheduler, "run_iteration", None)
)

assert "predict_batch" in inspect.getsource(
    scheduler.CTANativeScheduler.run_iteration
)

assert callable(
    getattr(factory, "create_cta_scheduler", None)
)

print("STAGED BATCH ADAPTER: PASS")
print("STAGED BATCH SCHEDULER: PASS")
print("STAGED FACTORY: PASS")
print("REAL MAX BACKEND VISIBLE: PASS")
print("NATIVE BATCH-2 IMPORT PREFLIGHT: PASS")
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i", "-w", "/workspace",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONPATH=/batch2/native_batch2_release_candidate:"
            "/workspace/artifacts/v1.168-max",
            ids[0], "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45
    )

    print(r.stdout[-4000:])
    print("EXIT CODE:", r.returncode)

except subprocess.TimeoutExpired:
    print("STOP: Import preflight exceeded 45 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MAX EXECUTIONS: ZERO")
PY
