podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-distinct-batch2-final \
  --format 'STATUS={{.State.Status}} IMAGE={{.ImageName}} MEMORY={{.HostConfig.Memory}} NETWORK={{.HostConfig.NetworkMode}} MOUNTS={{range .Mounts}}{{.Source}}:{{.Destination}};{{end}}'
