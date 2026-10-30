python3 -B - <<'PY'
from pathlib import Path
import subprocess, json, shutil, sys

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

source = dev / "native_batch2_release_candidate/maxserve_cta_extension"
target_root = repo / "artifacts/v1.168-max/cta_native_batch2_release_candidate"
target = target_root / "maxserve_cta_extension"

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

running = subprocess.check_output(P + ["ps", "-q"], text=True).split()
ids = [x for x in running if x.startswith("a176e284b50a")]

if len(ids) != 1:
    raise SystemExit("STOP: Expected 8766 container unavailable")

cid = ids[0]
info = json.loads(subprocess.check_output(
    P + ["inspect", cid], text=True
))[0]

# Verify /workspace really maps to this exact repository.
mounts = [
    m for m in info.get("Mounts", [])
    if m.get("Destination") == "/workspace"
]

if len(mounts) != 1:
    raise SystemExit("STOP: /workspace mount not uniquely identified")

host_mount = Path(mounts[0]["Source"]).resolve()

if host_mount != repo.resolve():
    raise SystemExit(
        "STOP: Unexpected /workspace source: " + str(host_mount)
    )

if not source.is_dir() or source.is_symlink():
    raise SystemExit("STOP: Validated staged package unavailable")

if any(p.is_symlink() for p in source.rglob("*")):
    raise SystemExit("STOP: Staged package contains symlinks")

if target_root.exists():
    raise SystemExit("STOP: Target already exists; will not overwrite")

if shutil.disk_usage(repo).free < 50 * 1024 * 1024:
    raise SystemExit("STOP: Insufficient workspace disk")

print("8766 WORKSPACE MOUNT: VERIFIED", flush=True)
print("STAGED SOURCE: VERIFIED", flush=True)

# Copy to a new directory only.
try:
    shutil.copytree(
        source, target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
except BaseException:
    if target_root.exists():
        shutil.rmtree(target_root)
    raise

print("ISOLATED NATIVE BATCH-2 PACKAGE: COPIED", flush=True)

code = r'''
import sys
import importlib
import inspect
from pathlib import Path

root = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate"
)

pkg = root / "maxserve_cta_extension"

required = [
    pkg / "cta_worker_adapter.py",
    pkg / "cta_native_scheduler.py",
    pkg / "cta_scheduler_factory.py",
    pkg / "cta_native_launcher.py"
]

assert all(p.is_file() for p in required)

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

for mod in (adapter, scheduler, factory):
    assert Path(mod.__file__).resolve().parent == pkg.resolve()

classes = [
    cls for _, cls in inspect.getmembers(adapter, inspect.isclass)
    if cls.__module__ == adapter.__name__
    and callable(getattr(cls, "predict_batch", None))
]

assert len(classes) == 1
assert "predict_batch" in inspect.getsource(
    scheduler.CTANativeScheduler.run_iteration
)

assert callable(getattr(factory, "create_cta_scheduler", None))
assert Path("/batch2/real_max_batch2_backend.py").is_file()

print("STAGED PACKAGE VISIBLE IN 8766: PASS", flush=True)
print("NATIVE BATCH ADAPTER IMPORT: PASS", flush=True)
print("NATIVE BATCH SCHEDULER IMPORT: PASS", flush=True)
print("NATIVE FACTORY IMPORT: PASS", flush=True)
print("REAL MAX BACKEND VISIBLE: PASS", flush=True)
print("8766 BATCH-2 INTEGRATION PREFLIGHT: PASS", flush=True)
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            cid, "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45
    )

    print(r.stdout[-3500:])
    print("EXIT CODE:", r.returncode)

except subprocess.TimeoutExpired:
    print("STOP: Import verification timed out")

print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MAX EXECUTIONS: ZERO")
print("LIVE HTTP BATCHING: NOT YET VALIDATED")
PY
