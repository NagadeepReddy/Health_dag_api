python3 - <<'PY'
from pathlib import Path
import ast, subprocess, json, shutil, urllib.request

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
overlay = base / "native_batch2_cached_overlay"
adapter = overlay / "cta_worker_adapter.py"
backend = base / "real_max_batch2_backend.py"
pkg = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
name = "cta-batch2-trace-8766-v2"

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

def call(*args):
    r = subprocess.run(pod + list(args), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()

assert adapter.is_file() and backend.is_file()
assert pkg.is_dir(), "STOP: Candidate package missing"

direct = pkg / "run_batch2_contract.py"
nested = pkg / "run" / "batch2_contract.py"
assert direct.is_file() or nested.is_file(), \
    "STOP: Batch contract module missing"

info = json.loads(call("inspect", name))[0]
assert any(m.get("Source") == str(overlay)
           for m in info["Mounts"]), "STOP: Container mismatch"

with urllib.request.urlopen(
    "http://127.0.0.1:8765/health", timeout=10
) as r:
    assert r.status == 200, "STOP: Original MAX unhealthy"

assert shutil.disk_usage(base).free > 1024**3, \
    "STOP: Low application storage"

source = adapter.read_text()
marker = "spec.loader.exec_module(module)"
assert source.count(marker) == 1

if 'mounted_pkg = Path("/batch2/cta_max")' not in source:
    lines = source.splitlines()
    index = next(i for i, line in enumerate(lines)
                 if marker in line)
    indent = lines[index][:len(lines[index]) -
                          len(lines[index].lstrip())]
    block = [
        indent + 'mounted_pkg = Path("/batch2/cta_max")',
        indent + 'if mounted_pkg.is_dir() and str(mounted_pkg) not in _cta_pkg.__path__:',
        indent + '    _cta_pkg.__path__.insert(0, str(mounted_pkg))'
    ]
    lines[index:index] = block
    updated_adapter = "\n".join(lines) + "\n"
else:
    updated_adapter = source

updated_backend = backend.read_text()
old = "from cta_max.run_batch2_contract import pack_two_requests"
new = "from cta_max.run.batch2_contract import pack_two_requests"

if not direct.is_file() and nested.is_file():
    assert old in updated_backend or new in updated_backend
    updated_backend = updated_backend.replace(old, new)

ast.parse(updated_adapter)
ast.parse(updated_backend)

changes = []
for path, content in [
    (adapter, updated_adapter),
    (backend, updated_backend)
]:
    if path.read_text() != content:
        backup = path.with_name(path.name + ".before_8766_import_fix")
        assert not backup.exists(), f"STOP: Backup exists: {backup}"
        changes.append((path, backup, content))

if info["State"]["Status"] == "running":
    call("stop", "-t", "20", name)
elif info["State"]["Status"] != "exited":
    raise RuntimeError("STOP: Unexpected container state")

for path, backup, content in changes:
    shutil.copy2(path, backup)
    path.write_text(content)

print("IMPORT BRIDGE: FIXED")
print("SYNTAX: PASS")
print("BACKUPS: PRESERVED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")

call("start", name)
print("ISOLATED MAX: RESTART REQUESTED")
print("HTTP READINESS: PENDING")
PY
