echo "=== BPLAN PORT ==="
ss -ltnp | grep ':18768 ' || echo "BPLAN PORT NOT LISTENING"

echo "=== BPLAN CONTAINERS ==="
podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format '{{.ID}} {{.Status}} {{.Names}} {{.Command}}'
