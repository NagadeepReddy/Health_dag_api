PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-postman-shm1g-test"

echo "=== CONTAINER STATUS ==="
$PODMAN inspect "$NAME" \
  --format 'STATUS={{.State.Status}} OOM={{.State.OOMKilled}}'

echo "=== NATIVE WORKER STARTUP ==="
$PODMAN exec "$NAME" /bin/sh -c '
echo "=== LATEST STARTUP EVENTS ==="
grep -Ei "factory entered|worker|ready|traceback|error|exception|timeout|listening|shutting down" /tmp/cta_postman_native.log | tail -n 25

echo "=== HTTP PORT ==="
/opt/venv/bin/python -B -c "
import socket
s=socket.socket()
s.settimeout(2)
print(\"PORT 18767:\", \"LISTENING\" if s.connect_ex((\"127.0.0.1\",18767)) == 0 else \"NOT LISTENING\")
s.close()
"
'
