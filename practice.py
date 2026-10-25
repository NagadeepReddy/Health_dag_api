P="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== SERVER FAILURE DETAILS ==="
$P logs --tail 120 cta-native-live 2>&1 |
  grep -v 'CTA WORKER RESPONSE IDS: \[\]' |
  tail -55

echo "=== PORT 8765 LISTENING? ==="
$P exec cta-native-live /opt/venv/bin/python - <<'PY'
import socket
s = socket.socket()
print("PORT STATUS:", s.connect_ex(("127.0.0.1", 8765)))
s.close()
PY
