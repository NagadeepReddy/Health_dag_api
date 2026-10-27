podman --root /application1/podman/storage --runroot /run/containers/storage logs --tail 100 cta-native-live 2>&1 | grep -Ei 'error|traceback|weight|encoding|q4_k' || true
