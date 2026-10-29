cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py")
candidate = Path("/application1/cta_max_native_release_candidate_20261028/cta_router.py")
backup = p.with_name("cta_router.py.before_300s_sync.bak")

assert p.is_file() and candidate.is_file(), "STOP: Router missing"

old = p.read_text()
assert old.count("asyncio.timeout(120)") == 1, "STOP: Original timeout differs"
assert "asyncio.timeout(300)" in candidate.read_text(), "STOP: Candidate not updated"
assert not backup.exists(), "STOP: Backup already exists"

new = old.replace("asyncio.timeout(120)", "asyncio.timeout(300)")
ast.parse(new)

backup.write_bytes(p.read_bytes())
p.write_text(new)

assert "asyncio.timeout(300)" in p.read_text()
print("ORIGINAL MAX ROUTER: 300 SECONDS")
print("RELEASE CANDIDATE ROUTER: 300 SECONDS")
print("TIMEOUT SYNCHRONIZATION: PASS")
print("BACKUP: CREATED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
