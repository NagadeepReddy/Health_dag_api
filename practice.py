timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-native-live \
  --format 'ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} Error={{.State.Error}} Started={{.State.StartedAt}} Finished={{.State.FinishedAt}}'
