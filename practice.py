podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=aal-triton-check

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 70 aal-triton-check
