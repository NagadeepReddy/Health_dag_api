PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== DISK ==="
df -h /application1

echo "=== CLEAN CONTAINER CONFIG ==="
$PODMAN inspect cta-clean-native-batch2 \
  --format 'Status={{.State.Status}} ReadOnly={{.HostConfig.ReadonlyRootfs}} Restart={{.HostConfig.RestartPolicy.Name}}'
