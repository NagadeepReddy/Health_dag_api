podman --root /application1/podman/storage --runroot /run/containers/storage ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
