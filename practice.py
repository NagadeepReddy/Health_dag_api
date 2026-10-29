cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/cta_max_native_release_candidate_20261028/cta_router.py")
backup = p.with_name("cta_router.py.before_timeout_fix.bak")

assert p.is_file(), "STOP: Native router missing"

source = p.read_text()
old = "asyncio.timeout(120)"
new = "asyncio.timeout(300)"

assert source.count(old) == 1, "STOP: Timeout definition differs"
assert not backup.exists(), "STOP: Backup already exists"

updated = source.replace(old, new)
ast.parse(updated)

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("NATIVE REQUEST TIMEOUT: 120 -> 300 SECONDS")
print("BACKUP: CREATED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
PY
