podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --no-trunc --filter name=cta-native-live

echo "=== CONTAINER DETAILS ==="

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-native-live \
  --format 'Running={{.State.Running}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}' 2>&1
