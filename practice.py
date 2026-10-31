podman --root /application1/podman/storage --runroot /run/containers/storage images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}' | grep -E 'REPOSITORY|modular|max|cta'
