cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
backup = Path(str(p) + ".pre_send_diagnostic.bak")
s = p.read_text()

old = "            self.response_queue.put_nowait(responses)"
new = (
    old + '\n'
    '            print("CTA RESPONSE QUEUE SEND: COMPLETED", '
    'len(responses), flush=True)'
)

if s.count(old) != 1:
    raise SystemExit("STOP: expected queue send not found exactly once")
if backup.exists():
    raise SystemExit("STOP: diagnostic backup already exists")
if shutil.disk_usage("/application1").free < 1024**3:
    raise SystemExit("STOP: insufficient disk space")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")

shutil.copy2(p, backup)
p.write_text(updated)

print("QUEUE SEND DIAGNOSTIC: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
