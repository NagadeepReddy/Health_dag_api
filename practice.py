stat -c '%A %a %U:%G %n' \
/application1/sajjna8/tfy_triton_work/rt-aal-upg-lead-v1/artifacts/v1.4/config \
/application1/sajjna8/tfy_triton_work/rt-aal-upg-lead-v1/artifacts/v1.4/config/config.json

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  image inspect \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  --format 'Container user={{.Config.User}}'
