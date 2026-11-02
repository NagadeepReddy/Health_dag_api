echo "=== PORT 18768 ==="
ss -ltnp | grep ':18768' || true

echo "=== RUNNING CONTAINERS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps --format 'NAME={{.Names}} STATUS={{.Status}} PID={{.Pid}}'
