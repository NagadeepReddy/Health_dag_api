podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  start aal-triton-check

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 100 aal-triton-check
