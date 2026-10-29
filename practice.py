podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' \
  | grep -Ei 'NAMES|cta|max'
