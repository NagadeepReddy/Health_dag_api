podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=cta-max-test \
  --format '{{.Names}} | {{.Status}}'
