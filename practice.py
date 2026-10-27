podman --root /application1/podman/storage --runroot /run/containers/storage ps -a --no-trunc --format '{{.ID}} | {{.Names}} | {{.Status}}' | grep -i cta
