podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect sharp_gates \
  --format 'NAME={{.Name}}
STATUS={{.State.Status}}
PID={{.State.Pid}}
STARTED={{.State.StartedAt}}
IMAGE={{.Config.Image}}
COMMAND={{json .Config.Cmd}}
MEMORY_LIMIT={{.HostConfig.Memory}}
MOUNTS={{json .Mounts}}'
