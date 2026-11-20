podman images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'triton|mlserver'
