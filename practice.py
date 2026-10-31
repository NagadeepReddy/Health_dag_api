PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

for NAME in $($PODMAN ps -a --format '{{.Names}}' | grep '^cta-'); do
  echo "=== $NAME ==="
  $PODMAN inspect "$NAME" \
    --format 'STATUS={{.State.Status}} MEMORY_BYTES={{.HostConfig.Memory}} NETWORK={{.HostConfig.NetworkMode}} MOUNTS={{range .Mounts}}{{.Destination}};{{end}}'
done

echo "READ-ONLY CHECK COMPLETE"
