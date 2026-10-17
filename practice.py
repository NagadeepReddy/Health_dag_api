
python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py")
backup = p.with_suffix(".py.before_unwrap_fix")

source = p.read_text()
old = 'worker_globals = ModelWorker.run.__globals__'
new = 'worker_globals = inspect.unwrap(ModelWorker.run).__globals__'

assert source.count(old) == 1, "STOP: Unexpected source structure"
assert not backup.exists(), "STOP: Backup already exists"

updated = source.replace(
    'from .cta_scheduler_factory import create_cta_scheduler',
    'import inspect\n\nfrom .cta_scheduler_factory import create_cta_scheduler',
    1
).replace(old, new, 1)

ast.parse(updated)
shutil.copy2(p, backup)
p.write_text(updated)

print("CTA WORKER HOOK TARGET FIXED — SYNTAX PASS")
print("BACKUP CREATED:", backup)
print("Original DS and MAX inference files unchanged")
PY
