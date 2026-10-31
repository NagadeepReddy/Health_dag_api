podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-distinct-batch2-final \
  --format 'STATUS={{.State.Status}} MEMORY={{.HostConfig.Memory}} NETWORK={{.HostConfig.NetworkMode}}{{println}}{{range .Mounts}}MOUNT={{.Source}} -> {{.Destination}}{{println}}{{end}}'
