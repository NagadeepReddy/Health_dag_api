podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  image inspect \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  --format 'Entrypoint={{.Config.Entrypoint}} Cmd={{.Config.Cmd}}'
