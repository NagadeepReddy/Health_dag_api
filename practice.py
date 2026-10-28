cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -B - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
original = p.read_text()

old = 'str(model_path).rstrip("/").endswith("/cta_native_model")'
new = 'str(model_path).rstrip("/").endswith(("/cta_native_model", "/core-artifact"))'

assert original.count(old) == 1, "Expected condition not found; no changes made"

updated = original.replace(old, new)
ast.parse(updated)

backup = p.with_suffix(".py.pre_path_fix.bak")
assert not backup.exists(), "Backup already exists; no changes made"

backup.write_text(original)
p.write_text(updated)

print("CTA FACTORY PATH MATCH: FIXED")
print("PYTHON SYNTAX: PASS")
PY
