PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"

STATUS=$($PODMAN inspect "$NAME" --format '{{.State.Status}}')
echo "CONTAINER STATUS: $STATUS"

if [ "$STATUS" = "running" ]; then
  $PODMAN exec -i "$NAME" /opt/venv/bin/python -B - <<'PY'
from pathlib import Path
import socket

p = Path("/tmp/cta_clean_http_retry.log")
print("=== NATIVE STARTUP LOG ===")
if p.is_file():
    lines = p.read_text(errors="replace").splitlines()
    for line in lines[-45:]:
        print(line[:300])
else:
    print("STARTUP LOG: MISSING")

print("\n=== HTTP LISTENER ===")
s = socket.socket()
s.settimeout(2)
print("PORT 18767:", "LISTENING" if s.connect_ex(("127.0.0.1", 18767)) == 0 else "NOT LISTENING")
s.close()
print("READ-ONLY CHECK COMPLETE")
PY
fi
