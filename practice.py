echo "=== ACTUAL LIVE CONTAINER ID ==="

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' /proc/326785/cgroup | head -1)

echo "CONTAINER ID: $CID"

if [ -n "$CID" ]; then
  podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    inspect --format \
    'NAME={{.Name}}
IMAGE={{.ImageName}}
AUTO_REMOVE={{.HostConfig.AutoRemove}}
MOUNTS={{json .Mounts}}' "$CID" \
    || echo "CONTAINER USES A DIFFERENT PODMAN STORE"
else
  echo "CONTAINER ID NOT FOUND IN CGROUP"
fi
