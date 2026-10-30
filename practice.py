python3 -B - <<'PY'
from pathlib import Path
import subprocess, json

base = Path("/application1")
dev = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
stage = dev / "native_batch2_release_candidate/maxserve_cta_extension"

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

required = [
    stage / "cta_worker_adapter.py",
    stage / "cta_native_scheduler.py",
    stage / "cta_scheduler_factory.py",
    stage / "cta_spawn_worker.py",
    dev / "real_max_batch2_backend.py",
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Missing " + str(p))

ids = []

for cid in subprocess.check_output(
    P + ["ps", "-q"], text=True
).split():
    info = json.loads(
        subprocess.check_output(
            P + ["inspect", cid], text=True
        )
    )[0]

    if any(
        m.get("Source") == str(dev)
        and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        ids.append(cid)

if len(ids) != 1:
    raise SystemExit("STOP: Existing development container unavailable")

code = r'''
import sys, inspect, importlib
from pathlib import Path

root = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2_release_candidate"
)

pkg = root / "maxserve_cta_extension"

assert pkg.is_dir(), "Staged package not visible"

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

assert Path(adapter.__file__).resolve() == (
    pkg / "cta_worker_adapter.py"
).resolve()

assert Path(scheduler.__file__).resolve() == (
    pkg / "cta_native_scheduler.py"
).resolve()

batch_classes = [
    c for _, c in inspect.getmembers(adapter, inspect.isclass)
    if c.__module__ == adapter.__name__
    and callable(getattr(c, "predict_batch", None))
]

assert len(batch_classes) == 1

assert callable(
    getattr(scheduler.CTANativeScheduler, "run_iteration", None)
)

assert "predict_batch" in inspect.getsource(
    scheduler.CTANativeScheduler.run_iteration
)

assert callable(getattr(factory, "create_cta_scheduler", None))

backend = Path("/batch2/real_max_batch2_backend.py")
assert backend.is_file()

print("STAGED ADAPTER IMPORT: PASS")
print("STAGED BATCH SCHEDULER IMPORT: PASS")
print("STAGED FACTORY IMPORT: PASS")
print("REAL MAX BACKEND: VISIBLE")
print("NATIVE BATCH-2 RUNTIME PREFLIGHT: PASS")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "PYTHONPATH=" + str(stage.parent) +
              ":/workspace/artifacts/v1.168-max",
        ids[0], "/opt/venv/bin/python", "-B", "-"
    ],
    input=code,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=45
)

print(r.stdout[-3500:])
print("EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
