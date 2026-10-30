python3 - <<'PY'
from pathlib import Path
import shutil, re, ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = base / "native_batch2_minimal_overlay"
dst = base / "native_batch2_cached_overlay"

assert src.is_dir(), "STOP: Working overlay missing"
assert not dst.exists(), "STOP: Test overlay already exists"

server = src / "cta_native_batch2_proven_server.py"
assert server.is_file(), "STOP: Server launcher missing"

code = server.read_text()
pattern = r'\bport\s*=\s*8765\b'

assert len(re.findall(pattern, code)) == 1, \
    "STOP: Port declaration differs"

updated = re.sub(pattern, "port=8766", code)
ast.parse(updated)

shutil.copytree(src, dst)
(dst / server.name).write_text(updated)

print("ISOLATED TEST OVERLAY: CREATED")
print("TEST PORT: 8766")
print("SYNTAX: PASS")
print("OPTIMIZED BACKEND: INSTALLED PREVIOUSLY")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE SERVER: UNCHANGED")
print("TEST SERVER: NOT STARTED")
PY
