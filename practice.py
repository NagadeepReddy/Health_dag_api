podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format 'table {{.ID}}\t{{.Status}}\t{{.Names}}'
