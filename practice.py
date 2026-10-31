podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== NATIVE MAX STARTUP ==="
tail -n 35 /tmp/cta_clean_http.log 2>&1

echo "=== HTTP LISTENER ==="
/opt/venv/bin/python -B -c "
import socket
s = socket.socket()
s.settimeout(2)
print(\"HTTP PORT 18767:\", \"LISTENING\" if s.connect_ex((\"127.0.0.1\",18767)) == 0 else \"NOT LISTENING\")
s.close()
"
'
