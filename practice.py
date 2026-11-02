python3 - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py")
s = p.read_text()

needle = '    async def bplan_spawn(*args, **kwargs):'
marker = '        print("BPLAN SPAWN HOOK ENTERED", flush=True)'

if marker in s:
    print("BPLAN SPAWN DIAGNOSTIC: ALREADY INSTALLED")
else:
    assert s.count(needle) == 1, "STOP: spawn function not found exactly once"
    s = s.replace(needle, needle + "\n" + marker, 1)
    ast.parse(s)
    p.write_text(s)
    print("BPLAN SPAWN DIAGNOSTIC: INSTALLED")

print("ORIGINAL DS AND CTA: UNCHANGED")
PY
