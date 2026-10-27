podman images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'modular|max|triton' || true
