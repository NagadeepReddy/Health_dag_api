podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-clean-batch2-http-20261030 \
  --format 'STATUS={{.State.Status}} EXIT_CODE={{.State.ExitCode}} OOM_KILLED={{.State.OOMKilled}} FINISHED={{.State.FinishedAt}}'
