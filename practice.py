podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/rt-aal-upg-lead-v1/artifacts/v1.4/config:/mnt/all-MiniLM-L6-v2:ro \
  --entrypoint /bin/sh \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'ls -l /mnt/all-MiniLM-L6-v2/config.json; grep -n model_type /mnt/all-MiniLM-L6-v2/config.json'
