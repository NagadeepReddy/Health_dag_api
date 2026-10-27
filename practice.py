podman --root /application1/podman/storage --runroot /run/containers/storage inspect cta-native-live --format '{{range .Mounts}}{{println .Source " -> " .Destination}}{{end}}'
