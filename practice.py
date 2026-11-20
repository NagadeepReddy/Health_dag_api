podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  start aal-triton-check

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 60 aal-triton-check
