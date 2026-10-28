cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
import os, signal, subprocess, time
from pathlib import Path

MARK = b"/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py"

podman = subprocess.run(
    ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage",
     "ps", "--format", "{{.Names}}"],
    capture_output=True, text=True
)

if podman.returncode != 0:
    raise SystemExit("STOP: Cannot verify active containers")

if any("cta" in name.lower() for name in podman.stdout.splitlines()):
    raise SystemExit("STOP: Active CTA container detected")

procs = {}

for entry in Path("/proc").iterdir():
    if not entry.name.isdigit():
        continue
    try:
        pid = int(entry.name)
        args = (entry / "cmdline").read_bytes().split(b"\0")
        stat = (entry / "stat").read_text()
        ppid = int(stat.rsplit(")", 1)[1].split()[1])
        procs[pid] = (ppid, args)
    except (OSError, ValueError, IndexError):
        continue

roots = [
    pid for pid, (_, args) in procs.items()
    if MARK in args and b"-B" in args
]

if not roots:
    print("NO LEFTOVER CTA TEST PROCESSES FOUND")
    raise SystemExit(0)

targets = set(roots)

changed = True
while changed:
    changed = False
    for pid, (ppid, args) in procs.items():
        if ppid in targets and pid not in targets:
            if any(b"python" in a or b"multiprocessing" in a for a in args):
                targets.add(pid)
                changed = True

print("=== CTA TEST PROCESSES TO STOP ===")
for pid in sorted(targets):
    print("PID:", pid, "PPID:", procs[pid][0])

print("=== SENDING GRACEFUL SIGTERM ===")

for pid in sorted(targets, reverse=True):
    try:
        os.kill(pid, signal.SIGTERM)
        print("SIGTERM SENT:", pid)
    except ProcessLookupError:
        pass
    except PermissionError:
        print("PERMISSION DENIED:", pid)

time.sleep(2)

remaining = [pid for pid in targets if Path(f"/proc/{pid}").exists()]

print("REMAINING PIDS:", remaining)
print("NO SIGKILL USED")
print("NO CONTAINERS DELETED")
print("DS CODE UNCHANGED")
PY

echo "=== MEMORY AFTER CTA CLEANUP ==="
free -h
