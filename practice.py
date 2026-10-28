echo "=== PODMAN RUNTIME STATE ==="
timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format 'table {{.ID}}\t{{.Status}}\t{{.Names}}'

echo "=== OVERLAY MOUNT TARGETS ==="
findmnt -rn -t overlay -o TARGET | head -30
