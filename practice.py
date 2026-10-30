CID=$(sed -nE 's@.*/container/([0-9a-f]{64}).*@\1@p' /proc/326785/cgroup | head -1)

echo "LIVE CONTAINER ID: $CID"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect --format \
  'NAME={{.Name}}
IMAGE={{.ImageName}}
AUTO_REMOVE={{.HostConfig.AutoRemove}}
COMMAND={{json .Config.Cmd}}
MOUNTS={{json .Mounts}}' "$CID" \
  || echo "STOP: Live container not managed by this Podman store"
