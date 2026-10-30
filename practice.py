echo "=== HTTP HEALTH ==="
curl --noproxy '*' -sS --max-time 5 \
  -o /dev/null -w 'HTTP: %{http_code}\n' \
  http://127.0.0.1:8765/health

echo "=== PORT 8765 ==="
ss -ltnp '( sport = :8765 )'

echo "=== NATIVE CONTAINER ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=cta-native-live \
  --format 'table {{.Names}}\t{{.Status}}\t{{.ID}}'
