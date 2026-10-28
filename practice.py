cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

old = '''        self.create_background_task(
            lambda: _cta_wait_for_healthy_worker(self._engine_queue)
        )
        print("CTA RECEIVER WAIT HOOK INSTALLED", flush=True)
'''

new = '''        # MAX starts its response worker inside __aenter__().
'''

if s.count(old) != 1:
    raise SystemExit("STOP: Expected lifecycle block not found exactly once; no changes")

updated = s.replace(old, new)
ast.parse(updated)

backup = p.with_name(p.name + ".pre_lifecycle_fix")
if backup.exists():
    raise SystemExit("STOP: Backup already exists; no changes")

backup.write_text(s)
p.write_text(updated)

print("CTA LIFECYCLE FIX: APPLIED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL MAX FILE: UNCHANGED")
print("DS CODE: UNCHANGED")
PY
