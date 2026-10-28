cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")
backup = Path(str(p) + ".pre_response_queue_fix.bak")
s = p.read_text()

old = '''        print("CTA WORKER RESPONSE IDS:", list(responses.keys()), flush=True)
        self.response_queue.put_nowait(responses)'''

new = '''        if responses:
            print("CTA WORKER RESPONSE IDS:", list(responses.keys()), flush=True)
            self.response_queue.put_nowait(responses)'''

if s.count(old) != 1:
    raise SystemExit("STOP: expected response block not found exactly once")

if backup.exists():
    raise SystemExit("STOP: backup already exists")

updated = s.replace(old, new, 1)
compile(updated, str(p), "exec")

if shutil.disk_usage("/application1").free < 1024**3:
    raise SystemExit("STOP: insufficient disk space")

shutil.copy2(p, backup)
p.write_text(updated)

print("EMPTY RESPONSE QUEUE FIX: INSTALLED")
print("BACKUP:", backup)
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
