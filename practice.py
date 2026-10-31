podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --timestamps --since 5m --tail 120 \
  cta-clean-native-batch2 2>&1 | tail -75
