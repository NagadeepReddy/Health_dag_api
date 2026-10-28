timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-native-live \
  --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} Error={{.State.Error}}'

echo "=== CTA NATIVE LAST LOGS ==="

timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 35 cta-native-live
