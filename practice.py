podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --format \
  'NAME={{.Names}} | ID={{.ID}} | STATUS={{.Status}} | IMAGE={{.Image}}' \
  | grep -Ei 'cta|batch2|max'
