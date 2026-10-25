P="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== HTTP LISTENER ==="
$P exec cta-native-live /opt/venv/bin/python -c '
import socket
s = socket.socket()
print("PORT 8765:", "LISTENING" if s.connect_ex(("127.0.0.1",8765)) == 0 else "NOT LISTENING", flush=True)
s.close()
'

echo "=== SERVER STARTUP / ERRORS ==="
$P logs cta-native-live 2>&1 | \
grep -Ev 'CTA WORKER RESPONSE IDS: \[\]|not use pretrained embedding|loaded Transfer Model' | \
tail -35
