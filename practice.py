python3 -B - <<'PY'
from pathlib import Path
import hashlib
import ast

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
source = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")
target = base / "real_max_batch2_backend.py"
adapter = base / "cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py"

assert source.is_file() and not source.is_symlink()
assert base.is_dir() and not base.is_symlink()
assert adapter.is_file() and not adapter.is_symlink()
assert (base / "cta_max/__init__.py").is_file()
assert not target.is_symlink()

data = source.read_bytes()
if target.exists():
    assert target.is_file() and target.read_bytes() == data, "STOP: Backend differs"
    print("BACKEND ALREADY IDENTICAL")
else:
    with target.open("xb") as f:
        f.write(data)
    print("BACKEND COPIED")

assert target.read_bytes() == data
print("BACKEND SHA256:", hashlib.sha256(data).hexdigest())

text = adapter.read_text()
replacements = {
    'Path("/batch2/real_max_batch2_backend.py")':
        'Path(__file__).resolve().parents[2] / "real_max_batch2_backend.py"',
    'Path("/batch2/cta_max")':
        'Path(__file__).resolve().parents[2] / "cta_max"',
}

updated = text
for old, new in replacements.items():
    assert updated.count(old) == 1 or new in updated, f"STOP: Unexpected adapter: {old}"
    updated = updated.replace(old, new)

ast.parse(updated)
if updated != text:
    adapter.write_text(updated)
    print("CLEAN ADAPTER PATHS UPDATED: 2")
else:
    print("CLEAN ADAPTER PATHS ALREADY UPDATED")

assert adapter.read_text() == updated
print("CLEAN BACKEND AND ADAPTER: VERIFIED")
print("ORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
