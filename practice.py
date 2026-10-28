timeout 10s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  events --stream=false \
  --since 2026-10-28T00:00:00 \
  --filter container=cta_env_e2e_1028 \
  --format '{{.Time}} {{.Status}} {{.ContainerExitCode}}' \
  | tail -20
