python3 - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_spawn_worker.py")
s = p.read_text()

old = "    def __call__(self):"
new = '    def __call__(self):\n        print("BPLAN FACTORY ENTERED", flush=True)'

if "BPLAN FACTORY ENTERED" in s:
    print("BPLAN FACTORY DIAGNOSTIC: ALREADY INSTALLED")
else:
    assert s.count(old) == 1, "STOP: unexpected factory structure"
    updated = s.replace(old, new, 1)
    ast.parse(updated)
    p.write_text(updated)
    print("BPLAN FACTORY DIAGNOSTIC: INSTALLED")

print("ORIGINAL DS AND CTA: UNCHANGED")
PY
