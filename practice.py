podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  inspect cta-clean-native-batch2 \
  --format '{{range .Mounts}}{{println .Source "=>" .Destination "RW=" .RW}}{{end}}'
