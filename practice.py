podman --root /application1/podman/storage \
       --runroot /application1/podman/run/storage \
       images --format '{{.Repository}}:{{.Tag}} | {{.ID}}'
