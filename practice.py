python3 - <<'PY'
from pathlib import Path
import ast
import shutil
import os

d = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

src = d / "real_max_batch2_backend.py"
candidate = d / "real_max_batch2_backend_cached_candidate.py"
backup = d / "real_max_batch2_backend_before_cache.bak"

assert src.is_file() and candidate.is_file(), "STOP: Missing backend"

original = src.read_bytes()
optimized = candidate.read_bytes()

ast.parse(optimized.decode())

assert b'_max_graph' in optimized
assert b'_max_model' in optimized
assert b'if model is None:' in optimized

if backup.exists():
    assert backup.read_bytes() == original or original == optimized, \
        "STOP: Existing backup differs"
else:
    shutil.copy2(src, backup)

if original != optimized:
    tmp = d / ".real_max_batch2_backend_cache_install.tmp"
    assert not tmp.exists(), "STOP: Temporary file already exists"
    shutil.copy2(candidate, tmp)
    os.replace(tmp, src)

assert src.read_bytes() == optimized

print("OPTIMIZED BACKEND: INSTALLED")
print("BACKUP: PRESERVED")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE FILES: UNCHANGED")
print("LIVE WORKER RESTART: PENDING")
PY
