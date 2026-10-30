python3 - <<'PY'
from pathlib import Path
import ast, shutil

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_cached_overlay/cta_native_scheduler.py")
assert p.is_file(), "STOP: Isolated scheduler missing"

src = p.read_text()
assert "CTA QUEUE SEND COMPLETE" not in src, "STOP: Already instrumented"

lines = src.splitlines()
a = [i for i,s in enumerate(lines) if s.strip() == "if not isinstance(results, (list, tuple)):"]
b = [i for i,s in enumerate(lines) if s.strip() == "self.response_queue.put_nowait(responses)"]

assert len(a) == len(b) == 1, "STOP: Scheduler structure differs"

for i in sorted([a[0], b[0]], reverse=True):
    indent = lines[i][:len(lines[i])-len(lines[i].lstrip())]
    if i == a[0]:
        lines.insert(i, indent + 'print("CTA BATCH RETURNED:", type(results).__name__, flush=True)')
    else:
        lines.insert(i+1, indent + 'print("CTA QUEUE SEND COMPLETE", flush=True)')
        lines.insert(i, indent + 'print("CTA QUEUE SEND BEGIN:", len(responses), flush=True)')

patched = "\n".join(lines) + "\n"
ast.parse(patched)

backup = p.with_suffix(".py.before_queue_trace")
assert not backup.exists(), "STOP: Backup already exists"
shutil.copy2(p, backup)
p.write_text(patched)

print("ISOLATED SCHEDULER TRACE: INSTALLED")
print("SYNTAX: PASS")
print("BACKUP: PRESERVED")
print("ORIGINAL DS: UNCHANGED")
print("WORKING MAX SERVER: UNCHANGED")
print("NEXT: ISOLATED HTTP RETEST")
PY
