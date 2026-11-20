podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  history --format '{{.CreatedBy}}' \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  | head -20
