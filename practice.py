
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler.py")
old = "from max.interfaces.scheduler import Scheduler, SchedulerProgress"
new = "from max.interfaces.scheduler import Scheduler\nfrom max.serve.scheduler.base import SchedulerProgress"

text = p.read_text()
if old not in text:
    raise SystemExit("STOP: Expected import not found; file unchanged")

updated = text.replace(old, new, 1)
ast.parse(updated)
p.write_text(updated)

print("CTA SCHEDULER IMPORT FIXED — SYNTAX PASS")
print("DS AND MAX INFERENCE FILES UNCHANGED")
PY
