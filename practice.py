cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast, re

p = Path("/application1/cta_max_native_release_candidate_20261028/cta_router.py")
backup = p.with_name("cta_router.py.before_timeout_trace.bak")

assert p.is_file(), "STOP: Router missing"
assert not backup.exists(), "STOP: Backup already exists"

source = p.read_text()
assert source.count("asyncio.timeout(300)") == 1, "STOP: Router timeout differs"

matches = list(re.finditer(
    r"(?m)^([ \t]*)except TimeoutError:\s*\n",
    source
))
assert len(matches) == 1, "STOP: Timeout handler differs"

m = matches[0]
indent = m.group(1) + "    "
insert = (
    indent + "import traceback\n"
    + indent + 'print("CTA TIMEOUT TRACEBACK:", flush=True)\n'
    + indent + "traceback.print_exc()\n"
)

updated = source[:m.end()] + insert + source[m.end():]
ast.parse(updated)

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("TIMEOUT DIAGNOSTIC: INSTALLED")
print("ROUTER TIMEOUT: 300 SECONDS")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
