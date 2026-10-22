cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()

old = 'api = sys.modules.get("max.serve.pipelines.api_server")'
new = 'from max.serve import api_server\n    api = api_server'

assert s.count(old) == 1, "Expected code not found; no changes made"

updated = s.replace(old, new)
compile(updated, str(p), "exec")
p.write_text(updated)

print("MAX API IMPORT PATH: FIXED")
print("SYNTAX: PASS")
PY
