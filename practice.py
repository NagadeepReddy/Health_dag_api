podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec bplan-debug sh -c 'env | grep -Ei "TELEMETRY|OTEL|MODULAR" || true'
