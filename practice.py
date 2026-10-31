podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 100 cta-clean-native-batch2 2>&1
