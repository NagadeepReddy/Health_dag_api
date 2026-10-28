cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import json, ast

root = Path("artifacts")
config = json.loads((root / "v1.168/model-settings.json").read_text())
p = root / "v1.168-max/maxserve_cta_extension/cta_spawn_worker.py"

values = {k: config[k] for k in ("modelId", "expThrottleLabel")}
source = p.read_text()
anchor = "        pipeline = CTA()"

assert source.count(anchor) == 1, "STOP: CTA initialization differs"
assert 'os.environ.setdefault("modelId"' not in source, "STOP: already patched"

insert = (
    '        import os\n'
    + ''.join(f'        os.environ.setdefault({k!r}, {v!r})\n'
              for k, v in values.items())
    + anchor
)
updated = source.replace(anchor, insert)
ast.parse(updated)

backup = p.with_suffix(".py.before_env_fix.bak")
assert not backup.exists(), "STOP: backup already exists"
backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("NATIVE WORKER ENV FIX: INSTALLED")
print("MODEL SETTINGS:", values)
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
