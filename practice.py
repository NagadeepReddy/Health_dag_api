podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format 'ID={{.ID}} | NAME={{.Names}} | STATUS={{.Status}} | IMAGE={{.Image}}'
