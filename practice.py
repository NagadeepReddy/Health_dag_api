cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import json, ast, shutil

root = Path("artifacts")
config = json.loads((root / "v1.168/model-settings.json").read_text())
extra = config["parameters"]["extra"]

p = root / "v1.168-max/maxserve_cta_extension/cta_spawn_worker.py"
source = p.read_text()
anchor = "        pipeline = CTA()"
backup = p.with_name(p.name + ".before_env_fix.bak")

assert source.count(anchor) == 1, "STOP: initialization anchor changed"
assert not backup.exists(), "STOP: backup already exists"
assert 'os.environ.setdefault("modelId"' not in source, "STOP: already patched"

values = {
    "modelId": extra["modelId"],
    "expThrottleLabel": extra["expThrottleLabel"]
}

insert = (
    '        import os\n'
    + ''.join(
        f'        os.environ.setdefault({k!r}, {v!r})\n'
        for k, v in values.items()
    )
    + anchor
)

updated = source.replace(anchor, insert)
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("NATIVE WORKER ENV FIX: INSTALLED")
print("BACKUP: PASS")
print("MODEL SETTINGS: PASS")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
