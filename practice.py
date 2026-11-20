podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=aal-triton-check

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --since 2m --tail 80 aal-triton-check
