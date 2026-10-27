podman --root /application1/podman/storage --runroot /run/containers/storage ps -a --format '{{.Names}} | {{.Status}} | {{.Image}}' | grep -Ei 'max|cta|modular' || true
