podman --root /application1/podman/storage --runroot /run/containers/storage images --format '{{.Repository}}:{{.Tag}} | {{.Size}}' | grep -Ei 'max|modular|cta'
