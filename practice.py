podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== LATEST MAX STARTUP RESULT ==="
tail -n 25 /tmp/cta_clean_http.log

echo "=== HTTP PORT CHECK ==="
/opt/venv/bin/python -B -c "
import socket
s = socket.socket()
s.settimeout(2)
result = s.connect_ex((\"127.0.0.1\", 18767))
print(\"HTTP LISTENER:\", \"PASS\" if result == 0 else \"NOT LISTENING\")
s.close()
"
'
