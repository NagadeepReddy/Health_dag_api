cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
import os
import signal
from pathlib import Path

roots = (121339, 123853, 148527)
children = (121386, 148578)
marker = b"/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py"

def info(pid):
    try:
        args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return args, int(stat[1]), stat[0]
    except (OSError, ValueError, IndexError):
        return None

verified = []

for pid in roots:
    data = info(pid)
    if data and marker in data[0] and data[2] != "Z":
        verified.append(pid)
        print("VERIFIED CTA PARENT:", pid)
    else:
        print("SKIP PARENT (not verified/already exited):", pid)

for pid in children:
    data = info(pid)
    if (data and data[1] in verified and data[2] != "Z"
            and any(b"python" in a for a in data[0])):
        verified.append(pid)
        print("VERIFIED CTA CHILD:", pid)
    else:
        print("SKIP CHILD:", pid)

print("=== STOPPING VERIFIED CTA PROCESSES ONLY ===")
for pid in reversed(verified):
    data = info(pid)
    if not data:
        continue
    if pid in roots and marker not in data[0]:
        continue
    if pid in children and data[1] not in roots:
        continue
    try:
        os.kill(pid, signal.SIGKILL)
        print("STOP SIGNAL SENT:", pid)
    except ProcessLookupError:
        print("ALREADY EXITED:", pid)

print("NO FILES DELETED")
print("NO OTHER CONTAINERS STOPPED")
print("DS CODE UNCHANGED")
PY

echo "=== MEMORY AFTER CLEANUP ==="
free -h

echo "=== REMAINING CTA PARENTS ==="
ps -p 121339,123853,148527 -o pid,stat,rss,args || true
