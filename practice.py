PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"

echo "=== CLEAN CONTAINER STATUS ==="
$PODMAN ps --filter name=cta-clean-batch2-http-20261030 \
  --format 'NAME={{.Names}} STATUS={{.Status}}'

echo "=== AVAILABLE HOST MEMORY ==="
free -h

echo "=== CLEAN CONTAINER MEMORY ==="
$PODMAN inspect cta-clean-batch2-http-20261030 \
  --format 'STATE={{.State.Status}} LIMIT={{.HostConfig.Memory}} NETWORK={{.HostConfig.NetworkMode}}'
