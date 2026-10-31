PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME=cta-clean-native-batch2

echo "=== CLEAN CONTAINER STATUS ==="
$PODMAN inspect "$NAME" \
  --format 'STATUS={{.State.Status}} OOM={{.State.OOMKilled}}'

echo "=== CLEAN NATIVE WORKER LOG ==="
$PODMAN logs --tail 65 "$NAME" 2>&1 | \
  grep -Ei 'worker|factory|ready|listening|error|exception|traceback|missing|failed|timeout|mojo|cache|permission|shutting down' | tail -35

echo "=== HOST HTTP PORT ==="
python3 -B - <<'PY'
import socket
s = socket.socket()
s.settimeout(2)
print("PORT 18767:", "LISTENING" if s.connect_ex(("127.0.0.1", 18767)) == 0 else "NOT LISTENING")
s.close()
PY
