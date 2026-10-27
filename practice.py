podman --root /application1/podman/storage --runroot /run/containers/storage logs --tail 60 cta_native 2>&1 | tail -60
