podman images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -i maven
