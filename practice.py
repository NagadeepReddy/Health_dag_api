podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect 0c95d4a8f887 \
  --format 'STATUS={{.State.Status}}{{println}}{{range .Mounts}}MOUNT={{.Source}} -> {{.Destination}}{{println}}{{end}}'
