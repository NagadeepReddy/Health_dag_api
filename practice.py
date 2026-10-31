podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /bin/sh -c '
echo "=== NATIVE MAX STARTUP LOG ==="
if test -f /tmp/cta_clean_http.log; then
  tail -n 45 /tmp/cta_clean_http.log
else
  echo "LOG NOT CREATED"
fi

echo "=== HTTP PORT 18767 ==="
/opt/venv/bin/python -B -c "
import socket
s = socket.socket()
s.settimeout(2)
result = s.connect_ex((\"127.0.0.1\", 18767))
print(\"LISTENING\" if result == 0 else \"NOT LISTENING\")
s.close()
"
'
