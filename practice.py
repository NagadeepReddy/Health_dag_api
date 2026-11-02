python3 - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

old = "from max.entrypoints import headless_workers"
new = "from max.entrypoints import workers as headless_workers"

assert s.count(old) == 1, "STOP: unexpected launcher import"

updated = s.replace(old, new)
ast.parse(updated)
p.write_text(updated)

print("BPLAN HEADLESS IMPORT: CORRECTED TO MATCH CTA")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
