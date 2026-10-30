PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import subprocess, json, ast, shutil, urllib.request

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
overlay = base / "native_batch2_cached_overlay"
adapter = overlay / "cta_worker_adapter.py"
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
name = "cta-batch2-trace-8766-v2"

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

def run(*args):
    r = subprocess.run(pod + list(args), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()

assert adapter.is_file(), "STOP: Adapter missing"

module_files = [
    candidate / "cta_max/run_batch2_contract.py",
    candidate / "cta_max/run/batch2_contract.py"
]
assert any(p.is_file() for p in module_files), \
    "STOP: Batch contract source not found"

info = json.loads(run("inspect", name))[0]
mounts = [m.get("Source") for m in info["Mounts"]]

assert str(overlay) in mounts, "STOP: Overlay mismatch"
assert str(candidate) in mounts, "STOP: Candidate mount missing"
assert info["State"]["Status"] in ("running", "exited")
assert info["HostConfig"]["Memory"] >= 5 * 1024**3

with urllib.request.urlopen(
    "http://127.0.0.1:8765/health", timeout=10
) as r:
    assert r.status == 200, "STOP: Original MAX unhealthy"

source = adapter.read_text()
marker = "spec.loader.exec_module(module)"
tag = "CTA_EXPLICIT_CONTRACT_IMPORT_V1"

assert source.count(marker) == 1, "STOP: Import location differs"
assert tag not in source, "STOP: Fix already installed"
assert shutil.disk_usage(base).free > 1024**3

bridge = '''
# CTA_EXPLICIT_CONTRACT_IMPORT_V1
import sys as _cta_sys
import importlib.util as _cta_importlib
_cta_contract_files = [
    Path("/batch2/cta_max/run_batch2_contract.py"),
    Path("/batch2/cta_max/run/batch2_contract.py"),
]
_cta_contract_file = next(
    (p for p in _cta_contract_files if p.is_file()), None
)
if _cta_contract_file is None:
    raise ModuleNotFoundError("CTA batch contract not mounted")
_cta_name = "cta_max.run_batch2_contract"
if _cta_name not in _cta_sys.modules:
    _cta_spec = _cta_importlib.spec_from_file_location(
        _cta_name, _cta_contract_file
    )
    if _cta_spec is None or _cta_spec.loader is None:
        raise RuntimeError("CTA batch contract loader unavailable")
    _cta_mod = _cta_importlib.module_from_spec(_cta_spec)
    _cta_sys.modules[_cta_name] = _cta_mod
    try:
        _cta_spec.loader.exec_module(_cta_mod)
    except BaseException:
        _cta_sys.modules.pop(_cta_name, None)
        raise
'''.strip("\n")

lines = source.splitlines()
index = next(i for i, line in enumerate(lines) if marker in line)
indent = lines[index][:len(lines[index])-len(lines[index].lstrip())]

inserted = [
    indent + line if line else ""
    for line in bridge.splitlines()
]

lines[index:index] = inserted
updated = "\n".join(lines) + "\n"
ast.parse(updated)

backup = adapter.with_name(
    "cta_worker_adapter.py.before_contract_import_fix"
)
assert not backup.exists(), "STOP: Backup already exists"

print("MODULE SOURCE:", next(str(p) for p in module_files if p.is_file()))

if info["State"]["Status"] == "running":
    run("stop", "-t", "20", name)

shutil.copy2(adapter, backup)
adapter.write_text(updated)

print("DIRECT CONTRACT IMPORT: INSTALLED")
print("SYNTAX: PASS")
print("BACKUP: PRESERVED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")

run("start", name)

print("ISOLATED MAX: RESTART REQUESTED")
print("HTTP READINESS: PENDING")
PY
