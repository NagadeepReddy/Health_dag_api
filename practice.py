POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' /proc/326785/cgroup | head -1)

if [ -n "$CID" ]; then
  "${POD[@]}" inspect --format \
  'NAME={{.Name}}
AUTO_REMOVE={{.HostConfig.AutoRemove}}
NETWORK={{.HostConfig.NetworkMode}}
ENTRYPOINT={{json .Config.Entrypoint}}
COMMAND={{json .Config.Cmd}}
CREATE_COMMAND={{json .Config.CreateCommand}}' "$CID"
else
  echo "STOP: Live container not found"
fi
