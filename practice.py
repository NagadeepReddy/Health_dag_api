podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-native-live \
  --format 'IMAGE={{.ImageName}}
ENTRYPOINT={{json .Config.Entrypoint}}
COMMAND={{json .Config.Cmd}}
MOUNTS={{range .Mounts}}{{.Source}} -> {{.Destination}}; {{end}}'
