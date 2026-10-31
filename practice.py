podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-clean-batch2-http-20261030 \
  /opt/venv/bin/python -B - <<'PY'
import os
import socket
from pathlib import Path

s = socket.socket()
s.settimeout(2)
active = s.connect_ex(("127.0.0.1", 18767)) == 0
s.close()

print("HTTP PORT 18767:", "LISTENING" if active else "NOT LISTENING")

found = []
for p in Path("/proc").iterdir():
    if not p.name.isdigit() or int(p.name) == os.getpid():
        continue
    try:
        args = (p / "cmdline").read_bytes().split(b"\0")
        if any(b"cta_native_launcher" in a for a in args) and \
           any(b"main()" in a for a in args):
            found.append(p.name)
    except OSError:
        continue

print("NATIVE LAUNCHER PIDS:", found or "NONE")
print("READ-ONLY CHECK COMPLETE")
PY
