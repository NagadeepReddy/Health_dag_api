podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format '{{.Repository}}:{{.Tag}} | {{.ID}}' \
  | grep -Ei 'max|modular|faiss'
