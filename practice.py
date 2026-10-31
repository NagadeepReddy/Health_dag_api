PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-postman-validated-20261030"

$PODMAN exec "$NAME" /bin/sh -c '
echo "=== NATIVE SERVER STATUS ==="
grep -Ei "server ready|worker ready|worker failed|worker died|error|timeout|listening|shutting down" /tmp/cta_postman_native.log | tail -n 15

echo "=== HTTP LISTENER ==="
/opt/venv/bin/python -B -c "
import socket
s=socket.socket()
s.settimeout(2)
print(\"PORT 18767:\", \"LISTENING\" if s.connect_ex((\"127.0.0.1\",18767)) == 0 else \"NOT LISTENING\")
s.close()
"
'
