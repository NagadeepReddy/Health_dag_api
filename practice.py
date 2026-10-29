podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  images --format '{{.Repository}}:{{.Tag}}  {{.ID}}' \
  | grep -Ei 'modular|max-full|cta-max' \
  || echo "NO MATCHING MAX IMAGE FOUND"
