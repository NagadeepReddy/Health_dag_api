podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-batch2-trace-8766-10g \
  --format 'IMAGE={{.ImageName}}
STATE={{.State.Status}}
EXIT={{.State.ExitCode}}
OOM={{.State.OOMKilled}}
CREATE={{json .Config.CreateCommand}}
ENTRYPOINT={{json .Config.Entrypoint}}
CMD={{json .Config.Cmd}}
WORKDIR={{.Config.WorkingDir}}
MOUNTS={{json .Mounts}}'
