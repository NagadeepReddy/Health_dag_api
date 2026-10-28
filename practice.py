podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps --no-trunc \
  --format 'ID={{.ID}} NAME={{.Names}} STATUS={{.Status}} IMAGE={{.Image}}'
